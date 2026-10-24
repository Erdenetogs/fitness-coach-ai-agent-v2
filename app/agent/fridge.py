"""Хөргөгчний зураг → орц таних → хэрэглэгчийн зорилгод тохирсон жор.

Claude-ийн зураг харах (vision) чадварыг ашиглана. Хариуг заавал тогтсон JSON бүтэцтэй
авахын тулд "submit_recipes" хэрэгслийг заавал дуудуулна (tool_choice)."""
import base64

from app import db, planner
from app.agent import llm

RECIPE_TOOL = {
    "name": "submit_recipes",
    "description": "Зурагнаас олсон орцууд болон санал болгох жоруудыг илгээнэ.",
    "input_schema": {
        "type": "object",
        "properties": {
            "ingredients": {"type": "array", "items": {"type": "string"}, "description": "Танигдсан орцууд, монголоор"},
            "recipes": {
                "type": "array",
                "minItems": 1, "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "kcal": {"type": "integer", "description": "Нэг порцын калори"},
                        "protein_g": {"type": "integer"},
                        "time_min": {"type": "integer"},
                        "uses": {"type": "array", "items": {"type": "string"}, "description": "Зурагнаас ашиглах орцууд"},
                        "extra": {"type": "array", "items": {"type": "string"}, "description": "Нэмж авах шаардлагатай орц"},
                        "steps": {"type": "array", "items": {"type": "string"}},
                        "why": {"type": "string", "description": "Хэрэглэгчийн зорилгод яагаад тохирох, нэг өгүүлбэр"},
                    },
                    "required": ["title", "kcal", "protein_g", "time_min", "uses", "steps", "why"],
                },
            },
        },
        "required": ["ingredients", "recipes"],
    },
}


def analyze(uid: int, image_bytes: bytes | None, media_type: str | None, typed: str = "") -> dict:
    user = db.get_user(uid) or {}
    n = planner.nutrition(user)
    memories = [m["text"] for m in db.get_memories(uid)]
    steps = [{"icon": "person_search", "text": "Профайл, калорийн зорилтыг уншсан"}]
    if memories:
        steps.append({"icon": "bookmark", "text": "Санах ой (харшил, дуршил)-г шалгасан"})

    if llm.is_live():
        try:
            data = _analyze_live(user, n, memories, image_bytes, media_type, typed)
            steps.append({"icon": "photo_camera", "text": "Зурагнаас орц таньсан" if image_bytes else "Орцын жагсаалтыг уншсан"})
            steps.append({"icon": "restaurant_menu", "text": f"{len(data['recipes'])} жор боловсруулсан"})
            return {**data, "agent_steps": steps, "target": n, "demo": False}
        except Exception as e:
            steps.append({"icon": "error", "text": f"AI алдаа ({type(e).__name__}) — демо хариу"})
    data = _mock(user, typed)
    steps.append({"icon": "photo_camera", "text": "Орц таньсан (демо)"})
    steps.append({"icon": "restaurant_menu", "text": f"{len(data['recipes'])} жор санал болгосон"})
    return {**data, "agent_steps": steps, "target": n, "demo": True}


def _analyze_live(user, n, memories, image_bytes, media_type, typed) -> dict:
    client = llm.get_client()
    goal = planner.GOALS.get(user.get("goal"), "Эрүүл чийрэг байх")
    prompt = (
        f"Хэрэглэгчийн зорилго: {goal}. Өдрийн калори {n['kcal']} ккал, уураг {n['protein_g']} г.\n"
        f"Санах ой: {'; '.join(memories) or 'байхгүй'}.\n"
        + (f"Хэрэглэгч бичсэн орцууд: {typed}\n" if typed else "")
        + "Зурагт (эсвэл жагсаалтад) байгаа орцуудыг тань. Тэдгээрийг голчлон ашигласан, оюутан 30 минутад хийж чадах "
          "2–3 жор монголоор санал болго. Харшил/дургүй хоол байвал оруулахгүй. submit_recipes-ээр илгээ."
    )
    content = []
    if image_bytes:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": media_type or "image/jpeg",
                       "data": base64.b64encode(image_bytes).decode()},
        })
    content.append({"type": "text", "text": prompt})
    resp = client.messages.create(
        model=llm.MODEL,
        max_tokens=2048,
        tools=[RECIPE_TOOL],
        tool_choice={"type": "tool", "name": "submit_recipes"},
        messages=[{"role": "user", "content": content}],
    )
    for block in resp.content:
        if block.type == "tool_use":
            return block.input
    raise ValueError("submit_recipes дуудагдсангүй")


def _mock(user: dict, typed: str) -> dict:
    ingredients = [s.strip() for s in typed.replace("،", ",").split(",") if s.strip()] or [
        "Өндөг", "Тахианы мах", "Будаа", "Брокколи", "Сонгино", "Вандуй"]
    lose = user.get("goal") == "lose"
    return {
        "ingredients": ingredients,
        "recipes": [
            {
                "title": "Тахиатай брокколи шарсан будаа",
                "kcal": 420 if lose else 560, "protein_g": 38, "time_min": 20,
                "uses": ["Тахианы мах", "Брокколи", "Будаа", "Өндөг"], "extra": ["Шар буурцгийн сүмс"],
                "steps": ["Тахианы махыг жижиглэн хайруулд 6 мин шарна", "Брокколи, сонгино нэмж 3 мин хутгана",
                          "Хүйтэн будаа, өндөг нэмээд сүмсээр амтлана"],
                "why": "Уураг ихтэй, нэг таваг хоолоор өдрийн уургийн гуравны нэгийг авна.",
            },
            {
                "title": "Ногоотой өндөгний омлет",
                "kcal": 310, "protein_g": 22, "time_min": 10,
                "uses": ["Өндөг", "Сонгино", "Вандуй"], "extra": [],
                "steps": ["3 өндгийг давстай хольж хутгана", "Сонгино, вандуйг 2 мин шарна", "Өндгөө хийж таглаад 4 мин болгоно"],
                "why": "Хурдан, хямд, өглөөний дасгалын дараа тохиромжтой.",
            },
        ],
    }
