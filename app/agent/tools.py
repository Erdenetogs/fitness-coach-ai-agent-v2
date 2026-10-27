"""Агентын хэрэгслүүд (tools).
Claude ямар хэрэгсэл дуудахаа өөрөө шийднэ. Энд хэрэгсэл бүрийн тайлбар (schema),
бодит ажиллах функц, frontend-д харагдах "агентын алхам"-ын текстийг тодорхойлно."""
import json

from app import db, planner, xp

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
                "title": {"type": "string", "description": "Өдрийн нэр, ж: 'Доод бие' эсвэл 'Амрах өдөр'"},
                "exercises": {
                    "type": "array",
                    "description": "Хоосон массив бол амрах өдөр болно.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "icon": {"type": "string", "description": "Material Symbols icon нэр, ж: fitness_center, directions_run, accessibility_new"},
                            "sets": {"type": "integer"},
                            "reps": {"type": "integer"},
                            "duration_min": {"type": "integer"},
                        },
                        "required": ["name"],
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
        "name": "save_memory",
        "description": (
            "Цаашид хэрэг болох хэрэглэгчийн тухай баримтыг санах ойд хадгална: гэмтэл, өвдөлт, "
            "дуртай/дургүй хоол, хуваарь, харшил гэх мэт. Нэг удаагийн жижиг яриаг бүү хадгал."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"fact": {"type": "string", "description": "Богино, гуравдагч биеэр: 'Зүүн өвдөг өвддөг'"}},
            "required": ["fact"],
        },
    },
]

STEP_LABELS = {
    "get_user_profile": ("person_search", "Профайлыг уншсан"),
    "get_workout_plan": ("calendar_month", "Дасгалын төлөвлөгөөг шалгасан"),
    "get_workout_history": ("history", "Дасгалын түүхийг шалгасан"),
    "get_progress": ("monitoring", "Жингийн явцыг шалгасан"),
    "update_workout_day": ("edit_calendar", "Төлөвлөгөөг өөрчилсөн"),
    "log_weight": ("scale", "Жинг бүртгэсэн"),
    "save_memory": ("bookmark_added", "Санах ойд хадгалсан"),
}


def step_for(name: str, args: dict) -> dict:
    icon, text = STEP_LABELS.get(name, ("build", name))
    if name == "update_workout_day":
        text = f"{args.get('day', '')} гарагийн дасгалыг өөрчилсөн"
    elif name == "log_weight":
        text = f"Жинг бүртгэсэн: {args.get('kg')} кг"
    elif name == "save_memory":
        text = f"Санах ойд хадгалсан: {args.get('fact', '')}"
    return {"icon": icon, "text": text}


def run_tool(uid: int, name: str, args: dict) -> dict:
    """Хэрэгслийг ажиллуулж, Claude-д буцаах үр дүнг dict хэлбэрээр өгнө."""
    user = db.get_user(uid) or {}
    if name == "get_user_profile":
        return {
            "name": user.get("name"), "age": user.get("age"), "gender": user.get("gender"),
            "height_cm": user.get("height_cm"), "weight_kg": user.get("weight_kg"),
            "goal": planner.GOALS.get(user.get("goal"), user.get("goal")),
            "level": planner.LEVELS.get(user.get("level"), user.get("level")),
            "days_per_week": user.get("days_per_week"),
            "equipment": planner.EQUIPMENT.get(user.get("equipment"), user.get("equipment")),
            "nutrition": planner.nutrition(user), "bmi": planner.bmi(user),
            "coach_level": xp.status(uid),
        }
    if name == "get_workout_plan":
        return {"today": planner.today_name(), "plan": db.get_plan(uid)}
    if name == "get_workout_history":
        return {"history": db.get_workout_history(uid, int(args.get("days") or 14))}
    if name == "get_progress":
        weights = db.get_weights(uid)
        change = round(weights[-1]["kg"] - weights[0]["kg"], 1) if len(weights) > 1 else 0
        return {"weights": weights, "change_kg": change}
    if name == "update_workout_day":
        plan = db.get_plan(uid)
        day = args["day"]
        exercises = args.get("exercises") or []
        plan[day] = {
            "focus": "custom" if exercises else "rest",
            "title": args.get("title") or ("Амрах өдөр" if not exercises else "Шинэчилсэн дасгал"),
            "exercises": [{**{"icon": "fitness_center"}, **e} for e in exercises],
        }
        db.save_plan(uid, plan)
        return {"ok": True, "day": day, "plan_day": plan[day]}
    if name == "log_weight":
        db.add_weight(uid, float(args["kg"]))
        return {"ok": True, "kg": args["kg"]}
    if name == "save_memory":
        db.add_memory(uid, args["fact"])
        return {"ok": True}
    return {"error": f"Тодорхойгүй хэрэгсэл: {name}"}


def as_text(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False)
