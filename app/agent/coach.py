"""AI дасгалжуулагч агент.

Ажиллах зарчим (agent loop):
  1. Хэрэглэгчийн мессеж + санах ой + сүүлийн яриаг Claude-д өгнө
  2. Claude хэрэгсэл дуудах шаардлагатай бол (tool_use) → бид тэр функцийг ажиллуулна
  3. Үр дүнг Claude-д буцааж өгнө → Claude дахин бодно
  4. Claude эцсийн хариугаа өгөх хүртэл давтана (дээд тал нь MAX_TURNS)
Дуудсан хэрэгсэл бүр "agent_steps" болж frontend-д харагдана.
"""
import re

from app import db, planner
from app.agent import llm
from app.agent.tools import TOOLS, as_text, run_tool, step_for

MAX_TURNS = 6

SYSTEM = """Чи бол FitCoach — их сургуулийн оюутнуудад зориулсан хувийн фитнесс дасгалжуулагч AI агент.

Дүрэм:
- Монгол хэлээр, найрсаг боловч товч (3–6 өгүүлбэр) хариул. Жагсаалт хэрэгтэй бол богино байлга.
- Хэрэглэгчийн өгөгдлийг таамаглахгүй — хэрэгслээр шалгаж байж хариул.
- Хэрэглэгч дасгал солих/хөнгөлөх/хүндрүүлэхийг хүсвэл get_workout_plan → update_workout_day-ээр төлөвлөгөөг бодитоор өөрчил.
- Гэмтэл, өвдөлт, хоолны дуршил, хуваарь зэрэг удаан хэрэг болох мэдээллийг save_memory-гоор хадгал.
- Хэрэглэгч жингээ хэлбэл log_weight-ээр бүртгэ.
- Хүчтэй өвдөлт, толгой эргэх, цээж өвдөх зэрэг шинж тэмдэг дурдвал дасгалаа зогсоож эмчид үзүүлэхийг зөвлө.
- Эмнэлгийн онош бүү тавь.
- Хэрэглэгч level, XP, streak-ийн талаар асуувал get_user_profile-аар шалгаад урамшуулж хариул. XP: дасгал дуусгах +40, хоол бүртгэх +15, өдрийн анхны чат +5.

Хэрэглэгчийн тухай санах ойд байгаа баримтууд:
{memories}
"""


def _memories_text(uid: int) -> str:
    mem = db.get_memories(uid)
    return "\n".join(f"- {m['text']}" for m in mem) or "- (одоогоор байхгүй)"


def chat(uid: int, message: str) -> dict:
    db.add_message(uid, "user", message)
    if llm.is_live():
        try:
            result = _chat_live(uid, message)
        except Exception as e:  # API алдаа гарсан ч сайт унахгүй
            result = _chat_mock(uid, message)
            result["reply"] += f"\n\n(AI холболтод алдаа гарсан тул демо хариу өглөө: {type(e).__name__})"
    else:
        result = _chat_mock(uid, message)
    db.add_message(uid, "assistant", result["reply"], result["agent_steps"])
    return result


def _chat_live(uid: int, message: str) -> dict:
    client = llm.get_client()
    history = db.get_messages(uid, limit=12)[:-1]  # сүүлийнх нь одоогийн мессеж
    messages = [{"role": m["role"], "content": m["content"]} for m in history if m["content"]]
    # Claude-д эхний мессеж заавал user байх ёстой
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    messages.append({"role": "user", "content": message})

    steps, plan_changed = [], False
    for _ in range(MAX_TURNS):
        resp = client.messages.create(
            model=llm.MODEL,
            max_tokens=1024,
            system=SYSTEM.format(memories=_memories_text(uid)),
            tools=TOOLS,
            messages=messages,
        )
        if resp.stop_reason != "tool_use":
            reply = "".join(b.text for b in resp.content if b.type == "text").strip()
            return {"reply": reply or "…", "agent_steps": steps, "plan_changed": plan_changed}

        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            out = run_tool(uid, block.name, block.input or {})
            steps.append(step_for(block.name, block.input or {}))
            plan_changed |= block.name == "update_workout_day"
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": as_text(out)})
        messages.append({"role": "user", "content": results})

    return {"reply": "Уучлаарай, энэ асуултыг дуусгаж чадсангүй. Арай өөрөөр асууж үзээрэй.",
            "agent_steps": steps, "plan_changed": plan_changed}


# ---------------- Демо горим (API түлхүүргүй үед) ----------------
def _chat_mock(uid: int, message: str) -> dict:
    """Түлхүүргүй үед ч агентын зан төлөвийг харуулах энгийн дүрмүүд.
    Бодит хэрэгслүүдийг дуудаж, өгөгдлийн санг үнэхээр өөрчилнө."""
    text = message.lower()
    steps = []
    user = db.get_user(uid) or {}

    def use(name, args=None):
        args = args or {}
        steps.append(step_for(name, args))
        return run_tool(uid, name, args)

    # 1) Жин бүртгэх: "жин 68.5", "68 кг боллоо"
    #    "жин хасахад 30 хоног" гэх мэт өөр тоог жин гэж андуурахгүйн тулд нэгжийг шалгана.
    m = re.search(r"(\d{2,3}(?:[.,]\d)?)\s*(кг|kg)", text)
    if not m and "жин" in text:
        m = re.search(r"(\d{2,3}(?:[.,]\d)?)(?!\s*(?:хоног|өдөр|мин|удаа|сет|ккал|калори|см|%|\d))", text)
    kg = float(m.group(1).replace(",", ".")) if m else None
    if kg is not None and 30 <= kg <= 250:
        use("log_weight", {"kg": kg})
        prog = use("get_progress")
        diff = prog["change_kg"]
        trend = (f"Эхлэлээс хойш {abs(diff)} кг {'буурсан' if diff < 0 else 'нэмэгдсэн'} байна." if diff
                 else "Энэ бол эхний бүртгэл — цаашид өөрчлөлтийг графикаар харуулна.")
        return {"reply": f"{kg} кг гэж бүртгэлээ. {trend} Ингээд тогтмол үргэлжлүүлээрэй!",
                "agent_steps": steps, "plan_changed": False}

    # 2) Өвдөлт / гэмтэл → санах ой + өнөөдрийн дасгалыг хөнгөлөх
    pain = next((w for w in ["өвдөг", "нуруу", "мөр", "бугуй", "шагай", "өвдөж", "гэмт"] if w in text), None)
    if pain:
        use("save_memory", {"fact": message.strip()[:80]})
        plan = use("get_workout_plan")
        day = plan["today"]
        light = [
            {"name": "Сунгалт", "icon": "self_improvement", "duration_min": 10},
            {"name": "Хөнгөн алхалт", "icon": "directions_walk", "duration_min": 20},
            {"name": "Планк", "icon": "horizontal_rule", "sets": 2, "reps": 20},
        ]
        use("update_workout_day", {"day": day, "title": "Сэргээх өдөр", "exercises": light, "reason": "өвдөлт"})
        return {"reply": (f"Ойлголоо. Үүнийг санах ойдоо хадгаллаа, цаашид төлөвлөгөө гаргахдаа анхаарна. "
                          f"Өнөөдрийн ({day}) дасгалыг сунгалт, хөнгөн алхалт бүхий сэргээх өдөр болгож өөрчиллөө. "
                          "Өвдөлт 2–3 хоногоос удаан үргэлжилбэл эмчид үзүүлээрэй."),
                "agent_steps": steps, "plan_changed": True}

    # 3) Дасгал солих / хүндрүүлэх / хөнгөлөх
    if any(w in text for w in ["хүндрүүл", "хэцүү болго", "нэм"]) and "дасгал" in text:
        plan = use("get_workout_plan")
        day = plan["today"]
        cur = plan["plan"].get(day, {})
        harder = [{**e, "sets": e.get("sets", 2) + 1} if "sets" in e else {**e, "duration_min": e.get("duration_min", 10) + 5}
                  for e in cur.get("exercises", [])]
        if harder:
            use("update_workout_day", {"day": day, "title": cur.get("title"), "exercises": harder, "reason": "хүндрүүлэх"})
            return {"reply": f"{day} гарагийн дасгал бүрт нэг сет (эсвэл 5 минут) нэмлээ. Хэт ядарвал хэлээрэй, буцааж тохируулна.",
                    "agent_steps": steps, "plan_changed": True}

    if any(w in text for w in ["сол", "өөрчл", "хөнгөл", "амар"]):
        plan = use("get_workout_plan")
        day = plan["today"]
        cur = plan["plan"].get(day, {})
        easier = [{**e, "sets": max(1, e.get("sets", 2) - 1)} if "sets" in e else {**e, "duration_min": max(5, e.get("duration_min", 10) - 5)}
                  for e in cur.get("exercises", [])]
        if easier:
            use("update_workout_day", {"day": day, "title": cur.get("title"), "exercises": easier, "reason": "хөнгөлөх"})
            return {"reply": f"{day} гарагийн дасгалыг хөнгөлж, сет бүрийг нэгээр цөөлөв. Дасгал хуудаснаас шинэчилсэн хувилбарыг харж болно.",
                    "agent_steps": steps, "plan_changed": True}
        return {"reply": f"Өнөөдөр ({day}) амрах өдөр байна. Хүсвэл хөнгөн сунгалт хийгээрэй.",
                "agent_steps": steps, "plan_changed": False}

    # 3б) Level / XP / streak
    if any(w in text for w in ["level", "xp", "оноо", "streak", "дараалал"]):
        lv = use("get_user_profile")["coach_level"]
        left = lv["need"] - lv["xp"]
        return {"reply": (f"Чиний coach одоо Level {lv['level']} ({lv['stage']}) байна, нийт {lv['total']} XP. "
                          f"Дараагийн level хүртэл {left} XP үлдлээ — нэг өдрийн дасгал дуусгахад +40 XP. "
                          + (f"{lv['streak']} өдөр дараалан идэвхтэй байна, тасралтгүй үргэлжлүүлээрэй!" if lv["streak"] else
                             "Өнөөдөр нэг дасгал хийгээд streak-ээ эхлүүлье!")),
                "agent_steps": steps, "plan_changed": False}

    # 4) Хоол / калори
    if any(w in text for w in ["хоол", "калори", "уураг", "жор", "идэх"]):
        prof = use("get_user_profile")
        n = prof["nutrition"]
        return {"reply": (f"Таны зорилго ({prof['goal']})-д өдөрт ойролцоогоор {n['kcal']} ккал, {n['protein_g']} г уураг хэрэгтэй. "
                          "Хоол хуудсанд хөргөгчнийхөө зургийг оруулбал байгаа орцоор чинь жор санал болгоно."),
                "agent_steps": steps, "plan_changed": False}

    # 5) Явц / тогтмол байдал
    if any(w in text for w in ["явц", "ахиц", "хэр", "түүх", "долоо хоног"]):
        hist = use("get_workout_history", {"days": 7})
        prog = use("get_progress")
        n_days = len(hist["history"])
        return {"reply": (f"Сүүлийн 7 хоногт {n_days} өдөр дасгал хийжээ. Жин эхлэлээс {prog['change_kg']:+.1f} кг. "
                          + ("Сайн байна, хэмнэлээ хадгалаарай!" if n_days >= 3 else "Энэ долоо хоногт дор хаяж 3 өдөр хийхийг зорьё.")),
                "agent_steps": steps, "plan_changed": False}

    # 6) Ерөнхий
    plan = use("get_workout_plan")
    today = plan["plan"].get(plan["today"], {})
    if today.get("exercises"):
        names = ", ".join(e["name"] for e in today["exercises"][:3])
        msg = f"Өнөөдрийн дасгал ({today['title']}): {names}. Дасгал солих, хөнгөлөх, жингээ бүртгэх, хоолны зөвлөгөө авах бол надад хэлээрэй."
    else:
        msg = "Өнөөдөр амрах өдөр. Сайн унтаж, ус сайн уугаарай. Асуух зүйл байвал хэлээрэй."
    return {"reply": f"Сайн уу, {user.get('name', '')}! {msg}", "agent_steps": steps, "plan_changed": False}
