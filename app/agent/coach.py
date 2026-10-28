"""AI дасгалжуулагч агент.

Ажиллах зарчим (agent loop):
  1. Хэрэглэгчийн мессеж + санах ой + сүүлийн яриаг Claude-д өгнө
  2. Claude хэрэгсэл дуудах шаардлагатай бол (tool_use) → бид тэр функцийг ажиллуулна
  3. Үр дүнг Claude-д буцааж өгнө → Claude дахин бодно
  4. Claude эцсийн хариугаа өгөх хүртэл давтана (дээд тал нь MAX_TURNS)
Дуудсан хэрэгсэл бүр "agent_steps" болж frontend-д харагдана.
"""
import re

from app import db, i18n, planner
from app.agent import llm
from app.agent.tools import TOOLS, as_text, run_tool, step_for

MAX_TURNS = 6

SYSTEM = """Чи бол FitCoach — их сургуулийн оюутнуудад зориулсан хувийн фитнесс дасгалжуулагч AI агент.

Дүрэм:
- Хэрэглэгчийн сонгосон хэлээр ({language}) найрсаг боловч товч (3–6 өгүүлбэр) хариул. Жагсаалт хэрэгтэй бол богино байлга.
- Хэрэглэгчийн өгөгдлийг таамаглахгүй — хэрэгслээр шалгаж байж хариул.
- Хэрэглэгч дасгал солих/хөнгөлөх/хүндрүүлэхийг хүсвэл get_workout_plan → update_workout_day-ээр төлөвлөгөөг бодитоор өөрчил.
  Төлөвлөгөөний гарагийн нэр (day) Монголоор хадгалагддаг тул хэрэгсэлд яг тэр нэрийг дамжуул.
- Гэмтэл, өвдөлт, хоолны дуршил, хуваарь зэрэг удаан хэрэг болох мэдээллийг save_memory-гоор хадгал.
- Хэрэглэгч жингээ хэлбэл log_weight-ээр бүртгэ.
- Хүчтэй өвдөлт, толгой эргэх, цээж өвдөх зэрэг шинж тэмдэг дурдвал дасгалаа зогсоож эмчид үзүүлэхийг зөвлө.
- Эмнэлгийн онош бүү тавь.
- Хэрэглэгч level, XP, streak-ийн талаар асуувал get_user_profile-аар шалгаад урамшуулж хариул. XP: дасгал дуусгах +40, хоол бүртгэх +15, өдрийн анхны чат +5.

Хэрэглэгчийн тухай санах ойд байгаа баримтууд:
{memories}
"""

# Демо горимын түлхүүр үгс — Монгол, Англи, Солонгос
KW_WEIGHT = ("жин", "weight", "체중", "몸무게")
KW_PAIN = ("өвдөг", "нуруу", "мөр", "бугуй", "шагай", "өвдөж", "гэмт",
           "knee", "back", "shoulder", "wrist", "ankle", "hurt", "pain", "injur",
           "무릎", "허리", "어깨", "손목", "발목", "아파", "아프", "통증", "부상")
KW_HARDER = ("хүндрүүл", "хэцүү болго", "нэм", "harder", "more", "add", "어렵게", "늘려", "강하게")
KW_WORKOUT = ("дасгал", "workout", "exercise", "training", "운동")
KW_EASIER = ("сол", "өөрчл", "хөнгөл", "амар", "easier", "change", "swap", "lighter", "rest",
             "쉽게", "바꿔", "바꾸", "가볍게", "줄여")
KW_LEVEL = ("level", "xp", "оноо", "streak", "дараалал", "레벨", "연속")
KW_FOOD = ("хоол", "калори", "уураг", "жор", "идэх", "food", "calorie", "protein", "recipe", "eat", "meal",
           "음식", "칼로리", "단백질", "레시피", "먹", "식단")
KW_PROGRESS = ("явц", "ахиц", "хэр", "түүх", "долоо хоног", "progress", "week", "history", "how am i",
               "진행", "기록", "이번 주", "어때")


def _memories_text(uid: int) -> str:
    mem = db.get_memories(uid)
    return "\n".join(f"- {m['text']}" for m in mem) or "- (одоогоор байхгүй)"


def chat(uid: int, message: str, lang: str = "mn") -> dict:
    db.add_message(uid, "user", message)
    if llm.is_live():
        try:
            result = _chat_live(uid, message, lang)
        except Exception as e:  # API алдаа гарсан ч сайт унахгүй
            result = _chat_mock(uid, message, lang)
            result["reply"] += "\n\n" + i18n.t("m.ai_error", lang, e=type(e).__name__)
    else:
        result = _chat_mock(uid, message, lang)
    db.add_message(uid, "assistant", result["reply"], result["agent_steps"])
    return result


def _chat_live(uid: int, message: str, lang: str = "mn") -> dict:
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
            system=SYSTEM.format(memories=_memories_text(uid), language=i18n.AI_LANG[i18n.norm(lang)]),
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
            steps.append(step_for(block.name, block.input or {}, lang))
            plan_changed |= block.name == "update_workout_day"
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": as_text(out)})
        messages.append({"role": "user", "content": results})

    return {"reply": i18n.t("m.fail", lang), "agent_steps": steps, "plan_changed": plan_changed}


# ---------------- Демо горим (API түлхүүргүй үед) ----------------
def _chat_mock(uid: int, message: str, lang: str = "mn") -> dict:
    """Түлхүүргүй үед ч агентын зан төлөвийг харуулах энгийн дүрмүүд.
    Бодит хэрэгслүүдийг дуудаж, өгөгдлийн санг үнэхээр өөрчилнө.
    Өгөгдлийн санд Монголоор хадгалж, хариуг хэрэглэгчийн хэлээр бичнэ."""
    text = message.lower()
    steps = []
    user = db.get_user(uid) or {}
    t = lambda key, **kw: i18n.t(key, lang, **kw)  # noqa: E731
    has = lambda words: any(w in text for w in words)  # noqa: E731

    def use(name, args=None):
        args = args or {}
        steps.append(step_for(name, args, lang))
        return run_tool(uid, name, args)

    # 1) Жин бүртгэх: "жин 68.5", "68 кг боллоо", "weight 70", "체중 70"
    #    "жин хасахад 30 хоног" гэх мэт өөр тоог жин гэж андуурахгүйн тулд нэгжийг шалгана.
    m = re.search(r"(\d{2,3}(?:[.,]\d)?)\s*(кг|kg)", text)
    if not m and has(KW_WEIGHT):
        m = re.search(r"(\d{2,3}(?:[.,]\d)?)(?!\s*(?:хоног|өдөр|мин|удаа|сет|ккал|калори|см|%|\d|day|min|rep|set|cal|cm|일|분|회|세트))", text)
    kg = float(m.group(1).replace(",", ".")) if m else None
    if kg is not None and 30 <= kg <= 250:
        use("log_weight", {"kg": kg})
        prog = use("get_progress")
        diff = prog["change_kg"]
        trend = (t("m.trend_change", d=abs(diff), dir=t("m.dir_down" if diff < 0 else "m.dir_up")) if diff
                 else t("m.trend_first"))
        return {"reply": t("m.weight_logged", kg=kg, trend=trend), "agent_steps": steps, "plan_changed": False}

    # 2) Өвдөлт / гэмтэл → санах ой + өнөөдрийн дасгалыг хөнгөлөх
    if has(KW_PAIN):
        use("save_memory", {"fact": message.strip()[:80]})
        plan = use("get_workout_plan")
        day = plan["today"]
        light = [
            {"name": "Сунгалт", "icon": "self_improvement", "duration_min": 10},
            {"name": "Хөнгөн алхалт", "icon": "directions_walk", "duration_min": 20},
            {"name": "Планк", "icon": "horizontal_rule", "sets": 2, "reps": 20},
        ]
        use("update_workout_day", {"day": day, "title": "Сэргээх өдөр", "exercises": light, "reason": "өвдөлт"})
        return {"reply": t("m.pain", day=i18n.weekday(day, lang)), "agent_steps": steps, "plan_changed": True}

    # 3) Дасгал солих / хүндрүүлэх / хөнгөлөх
    if has(KW_HARDER) and has(KW_WORKOUT):
        plan = use("get_workout_plan")
        day = plan["today"]
        cur = plan["plan"].get(day, {})
        harder = [{**e, "sets": e.get("sets", 2) + 1} if "sets" in e else {**e, "duration_min": e.get("duration_min", 10) + 5}
                  for e in cur.get("exercises", [])]
        if harder:
            use("update_workout_day", {"day": day, "title": cur.get("title"), "exercises": harder, "reason": "хүндрүүлэх"})
            return {"reply": t("m.harder", day=i18n.weekday(day, lang)), "agent_steps": steps, "plan_changed": True}

    if has(KW_EASIER):
        plan = use("get_workout_plan")
        day = plan["today"]
        cur = plan["plan"].get(day, {})
        easier = [{**e, "sets": max(1, e.get("sets", 2) - 1)} if "sets" in e else {**e, "duration_min": max(5, e.get("duration_min", 10) - 5)}
                  for e in cur.get("exercises", [])]
        if easier:
            use("update_workout_day", {"day": day, "title": cur.get("title"), "exercises": easier, "reason": "хөнгөлөх"})
            return {"reply": t("m.easier", day=i18n.weekday(day, lang)), "agent_steps": steps, "plan_changed": True}
        return {"reply": t("m.rest_today", day=i18n.weekday(day, lang)), "agent_steps": steps, "plan_changed": False}

    # 3б) Level / XP / streak
    if has(KW_LEVEL):
        use("get_user_profile")
        from app import xp  # тойрог import-оос сэргийлнэ
        lv = xp.status(uid, lang)
        left = lv["need"] - lv["xp"]
        return {"reply": (t("m.level", level=lv["level"], stage=lv["stage"], total=lv["total"], left=left)
                          + (t("m.streak_yes", n=lv["streak"]) if lv["streak"] else t("m.streak_no"))),
                "agent_steps": steps, "plan_changed": False}

    # 4) Хоол / калори
    if has(KW_FOOD):
        prof = use("get_user_profile")
        n = prof["nutrition"]
        return {"reply": t("m.food", goal=t(f"goal.{user.get('goal', 'fit')}"), kcal=n["kcal"], p=n["protein_g"]),
                "agent_steps": steps, "plan_changed": False}

    # 5) Явц / тогтмол байдал
    if has(KW_PROGRESS):
        hist = use("get_workout_history", {"days": 7})
        prog = use("get_progress")
        n_days = len(hist["history"])
        return {"reply": (t("m.progress", n=n_days, ch=f"{prog['change_kg']:+.1f}")
                          + t("m.prog_good" if n_days >= 3 else "m.prog_push")),
                "agent_steps": steps, "plan_changed": False}

    # 6) Ерөнхий
    plan = use("get_workout_plan")
    today = plan["plan"].get(plan["today"], {})
    if today.get("exercises"):
        names = ", ".join(i18n.exercise(e["name"], lang) for e in today["exercises"][:3])
        msg = t("m.today_ex", title=i18n.day_title(today, lang), names=names)
    else:
        msg = t("m.today_rest")
    return {"reply": t("m.hello", name=user.get("name", ""), msg=msg), "agent_steps": steps, "plan_changed": False}
