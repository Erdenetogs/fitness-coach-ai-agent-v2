"""Агентын хэрэгслүүд (tools).
Claude ямар хэрэгсэл дуудахаа өөрөө шийднэ. Энд хэрэгсэл бүрийн тайлбар (schema),
бодит ажиллах функц, frontend-д харагдах "агентын алхам"-ын текстийг тодорхойлно."""
import json
from unicodedata import name

from app import db, i18n, planner, xp

TOOLS = [
    {
        "name": "get_user_profile",
        "description": "Хэрэглэгчийн профайл: нас, хүйс, өндөр, жин, зорилго, түвшин, долоо хоногт хэдэн өдөр дасгал хийх, багаж, өдрийн калорийн зорилт, coach-ийн level/XP ба дараалсан идэвхтэй өдөр (streak).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_workout_plan",
        "description": "Долоо хоногийн одоогийн дасгалын төлөвлөгөө ба өнөөдөр аль өдөр болохыг буцаана.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_workout_history",
        "description": "Сүүлийн N өдөрт хийж дуусгасан дасгалууд. Хэрэглэгч хэр тогтмол дасгал хийж байгааг мэдэхэд ашигла.",
        "input_schema": {
            "type": "object",
            "properties": {"days": {"type": "integer", "description": "Хэдэн өдрийн түүх (анхдагч 14)"}},
        },
    },
    {
        "name": "get_progress",
        "description": "Жингийн түүх (огноо, кг) ба эхлэлээс хэдэн кг өөрчлөгдсөн.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "update_workout_day",
        "description": (
            "Нэг өдрийн дасгалуудыг бүхэлд нь шинээр солино. Хэрэглэгч дасгал солих, хөнгөлөх, хүндрүүлэх, "
            "өвдөлтөөс болж өөрчлөхийг хүсвэл ашигла. Эхлээд get_workout_plan-аар одоогийнхыг хар."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "day": {"type": "string", "enum": planner.WEEKDAYS},
                "title": {"type": "string", "description": "Өдрийн нэр МОНГОЛООР, ж: 'Доод бие' эсвэл 'Амрах өдөр'"},
                "title_en": {"type": "string", "description": "Same day title in English"},
                "title_ko": {"type": "string", "description": "Same day title in Korean"},
                "exercises": {
                    "type": "array",
                    "description": "Хоосон массив бол амрах өдөр болно.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Дасгалын нэр МОНГОЛООР (хэрэглэгч аль ч хэлээр бичсэн байсан). "
                                     "Төлөвлөгөөнд байгаа дасгал бол яг тэр нэрийг ашигла"},
                            "name_en": {"type": "string", "description": "The same exercise name in English"},
                            "name_ko": {"type": "string", "description": "The same exercise name in Korean"},
                            "icon": {"type": "string", "description": "Material Symbols icon нэр, ж: fitness_center, directions_run, accessibility_new"},
                            "sets": {"type": "integer"},
                            "reps": {"type": "integer"},
                            "duration_min": {"type": "integer"},
                        },
                        "required": ["name", "name_en", "name_ko"],
                    },
                },
                "reason": {"type": "string", "description": "Яагаад өөрчилсөн тухай нэг өгүүлбэр"},
            },
            "required": ["day", "exercises", "reason"],
        },
    },
    {
        "name": "log_weight",
        "description": "Хэрэглэгчийн өнөөдрийн жинг (кг) бүртгэнэ.",
        "input_schema": {
            "type": "object",
            "properties": {"kg": {"type": "number"}},
            "required": ["kg"],
        },
    },
    {
        "name": "mark_workout_done",
        "description": "Хэрэглэгч өнөөдрийн дасгалаа хийж дуусгасан гэж хэлэхэд "
                       "өнөөдрийн бүх дасгалыг дууссан гэж тэмдэглэж, XP өгнө.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "save_memory",
        "description": (
            "Цаашид хэрэг болох хэрэглэгчийн тухай баримтыг санах ойд хадгална: гэмтэл, өвдөлт, "
            "дуртай/дургүй хоол, хуваарь, харшил гэх мэт. Нэг удаагийн жижиг яриаг бүү хадгал."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"fact": {"type": "string", "description": "Богино, гуравдагч биеэр: 'Шалгалтын үеэр завгүй'"}},
            "required": ["fact"],
        },
    },
    {
        "name": "forget_memory",
        "description": (
            "Хэрэглэгч санах ойгоос мэдээлэл устгахыг хүсвэл (ж: 'шалгалт дууссан, мартаарай') ашигла. "
            "Системийн зааврын санах ойн жагсаалтаас [id N]-ийг аваад дамжуул."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"memory_id": {"type": "integer", "description": "Санах ойн [id N] дугаар"}},
            "required": ["memory_id"],
        },
    },
]

STEP_ICONS = {
    "get_user_profile": "person_search",
    "get_workout_plan": "calendar_month",
    "get_workout_history": "history",
    "get_progress": "monitoring",
    "update_workout_day": "edit_calendar",
    "log_weight": "scale",
    "save_memory": "bookmark_added",
    "forget_memory": "bookmark_remove",
    "mark_workout_done": "task_alt",
}


def step_for(name: str, args: dict, lang: str = "mn") -> dict:
    """Frontend-д харагдах "агентын алхам" — хэрэглэгчийн сонгосон хэлээр."""
    icon = STEP_ICONS.get(name, "build")
    if name == "update_workout_day":
        text = i18n.t("step.update_workout_day", lang, day=i18n.weekday(args.get("day", ""), lang))
    elif name == "log_weight":
        text = i18n.t("step.log_weight", lang, kg=args.get("kg"))
    elif name == "save_memory":
        text = i18n.t("step.save_memory", lang, fact=args.get("fact", ""))
    elif name == "forget_memory":
        text = i18n.t("step.forget_memory", lang)
    elif name in STEP_ICONS:
        text = i18n.t(f"step.{name}", lang)
    else:
        text = name
    return {"icon": icon, "text": text}


def _plan_in_language(plan: dict, lang: str) -> list[dict]:
    """Төлөвлөгөөг хэрэглэгчийн хэлээр — сайт дээр харагддагтай яг ижил нэрээр.
    Ингэснээр AI англи/солонгос хариундаа монгол үг холихгүй, сайттай ижил нэр хэрэглэнэ."""
    return [{"day_key": d, "day": i18n.weekday(d, lang), "title": i18n.day_title(plan.get(d, {}), lang),
             "exercises": [i18n.exercise(e, lang) for e in plan.get(d, {}).get("exercises", [])]}
            for d in planner.WEEKDAYS]


def run_tool(uid: int, name: str, args: dict, lang: str = "mn") -> dict:
    """Хэрэгслийг ажиллуулж, Claude-д буцаах үр дүнг dict хэлбэрээр өгнө."""
    user = db.get_user(uid) or {}
    if name == "get_user_profile":
        return {
            "name": user.get("name"), "age": user.get("age"), "gender": user.get("gender"),
            "height_cm": user.get("height_cm"), "weight_kg": user.get("weight_kg"),
            "goal": i18n.t(f"goal.{user.get('goal')}", lang),
            "level": i18n.t(f"level.{user.get('level')}", lang),
            "days_per_week": user.get("days_per_week"),
            "equipment": i18n.t(f"equip.{user.get('equipment')}", lang),
            "nutrition": planner.nutrition(user), "bmi": planner.bmi(user),
            "coach_level": xp.status(uid, lang),
        }
    if name == "get_workout_plan":
        result = {"today": planner.today_name(), "plan": db.get_plan(uid)}
        if lang != "mn":
            result["today_in_user_language"] = i18n.weekday(result["today"], lang)
            result["plan_in_user_language"] = _plan_in_language(result["plan"], lang)
        return result
    if name == "get_workout_history":
        try:
            days = int(args.get("days") or 14)
        except (TypeError, ValueError):
            days = 14
        return {"history": db.get_workout_history(uid, max(1, min(90, days)))}
    if name == "get_progress":
        weights = db.get_weights(uid)
        change = round(weights[-1]["kg"] - weights[0]["kg"], 1) if len(weights) > 1 else 0
        return {"weights": weights, "change_kg": change}
    # Доорх хэрэгслүүд өгөгдөл өөрчилдөг тул AI-ийн өгсөн утгыг шалгаж байж хадгална.
    # Алдаатай бол {"error": ...} буцаавал Claude өөрөө засаад дахин дуудна.
    if name == "update_workout_day":
        day = args.get("day")
        if day not in planner.WEEKDAYS:
            return {"error": f"day нь эдгээрийн нэг байх ёстой: {', '.join(planner.WEEKDAYS)}"}
        keep = ("name", "name_en", "name_ko", "icon", "sets", "reps", "duration_min")
        exercises = [{k: e[k] for k in keep if e.get(k) not in (None, "")}
                     for e in (args.get("exercises") or []) if isinstance(e, dict) and e.get("name")][:10]
        for e in exercises:
            for k in ("name", "name_en", "name_ko"):
                if k in e:
                    e[k] = str(e[k]).strip()[:60]
            if e["name"] in i18n.EXERCISES:  # мэддэг дасгал бол бидний орчуулгыг ашиглана
                e.pop("name_en", None), e.pop("name_ko", None)
        plan = db.get_plan(uid)
        plan[day] = {
            "focus": "custom" if exercises else "rest",
            "title": str(args.get("title") or ("Амрах өдөр" if not exercises else "Шинэчилсэн дасгал"))[:40],
            "exercises": [{**{"icon": "fitness_center"}, **e} for e in exercises],
        }
        if exercises and args.get("title"):
            for k in ("title_en", "title_ko"):
                if args.get(k):
                    plan[day][k] = str(args[k]).strip()[:40]
        db.save_plan(uid, plan)
        return {"ok": True, "day": day, "plan_day": plan[day]}
    if name == "log_weight":
        try:
            kg = round(float(args.get("kg")), 1)
        except (TypeError, ValueError):
            return {"error": "kg нь тоо байх ёстой"}
        if not 25 <= kg <= 300:
            return {"error": "Жин 25–300 кг хооронд байх ёстой. Хэрэглэгчээс дахин асуу."}
        db.add_weight(uid, kg)
        return {"ok": True, "kg": kg}
    if name == "mark_workout_done":
        today = planner.today_name()
        exercises = db.get_plan(uid).get(today, {}).get("exercises", [])
        if not exercises:
            return {"error": "Өнөөдөр амрах өдөр — тэмдэглэх дасгал алга."}
        for e in exercises:
            db.set_exercise_done(uid, e["name"], True)
        gained = xp.award(uid, "workout", db.today(), lang)
        return {"ok": True, "day": today, "done": [e["name"] for e in exercises],
                "xp": gained["gained"] if gained else 0}
    if name == "save_memory":
        fact = str(args.get("fact") or "").strip()[:200]
        if not fact:
            return {"error": "fact хоосон байна"}
        db.add_memory(uid, fact)
        return {"ok": True}
    if name == "forget_memory":
        try:
            mid = int(args.get("memory_id"))
        except (TypeError, ValueError):
            return {"error": "memory_id нь тоо байх ёстой"}
        match = [m for m in db.get_memories(uid) if m["id"] == mid]
        if not match:
            return {"error": f"[id {mid}] санах ой олдсонгүй"}
        db.delete_memory(uid, mid)
        return {"ok": True, "deleted": match[0]["text"]}
    return {"error": f"Тодорхойгүй хэрэгсэл: {name}"}


def as_text(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False)
