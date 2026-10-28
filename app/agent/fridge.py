"""Хөргөгчний зураг → орц таних → хэрэглэгчийн зорилгод тохирсон жор.

Claude-ийн зураг харах (vision) чадварыг ашиглана. Хариуг заавал тогтсон JSON бүтэцтэй
авахын тулд "submit_recipes" хэрэгслийг заавал дуудуулна (tool_choice)."""
import base64

from app import db, i18n, planner
from app.agent import llm

RECIPE_TOOL = {
    "name": "submit_recipes",
    "description": "Зурагнаас олсон орцууд болон санал болгох жоруудыг илгээнэ.",
    "input_schema": {
        "type": "object",
        "properties": {
            "ingredients": {"type": "array", "items": {"type": "string"}, "description": "Танигдсан орцууд, хэрэглэгчийн хэлээр"},
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


def analyze(uid: int, image_bytes: bytes | None, media_type: str | None, typed: str = "", lang: str = "mn") -> dict:
    user = db.get_user(uid) or {}
    n = planner.nutrition(user)
    memories = [m["text"] for m in db.get_memories(uid)]
    t = lambda key, **kw: i18n.t(key, lang, **kw)  # noqa: E731
    steps = [{"icon": "person_search", "text": t("step.f_profile")}]
    if memories:
        steps.append({"icon": "bookmark", "text": t("step.f_memory")})

    if llm.is_live():
        try:
            data = _analyze_live(user, n, memories, image_bytes, media_type, typed, lang)
            steps.append({"icon": "photo_camera", "text": t("step.f_photo") if image_bytes else t("step.f_list")})
            steps.append({"icon": "restaurant_menu", "text": t("step.f_recipes", n=len(data["recipes"]))})
            return {**data, "agent_steps": steps, "target": n, "demo": False}
        except Exception as e:
            steps.append({"icon": "error", "text": t("step.f_error", e=type(e).__name__)})
    data = _mock(user, typed, lang)
    steps.append({"icon": "photo_camera", "text": t("step.f_demo_photo")})
    steps.append({"icon": "restaurant_menu", "text": t("step.f_suggested", n=len(data["recipes"]))})
    return {**data, "agent_steps": steps, "target": n, "demo": True}


def _analyze_live(user, n, memories, image_bytes, media_type, typed, lang="mn") -> dict:
    client = llm.get_client()
    goal = planner.GOALS.get(user.get("goal"), "Эрүүл чийрэг байх")
    prompt = (
        f"Хэрэглэгчийн зорилго: {goal}. Өдрийн калори {n['kcal']} ккал, уураг {n['protein_g']} г.\n"
        f"Санах ой: {'; '.join(memories) or 'байхгүй'}.\n"
        + (f"Хэрэглэгч бичсэн орцууд: {typed}\n" if typed else "")
        + "Зурагт (эсвэл жагсаалтад) байгаа орцуудыг тань. Тэдгээрийг голчлон ашигласан, оюутан 30 минутад хийж чадах "
          "2–3 жор санал болго. Харшил/дургүй хоол байвал оруулахгүй. submit_recipes-ээр илгээ.\n"
        + f"Орц, жорын нэр, алхам, тайлбарыг бүгдийг {i18n.AI_LANG[i18n.norm(lang)]} хэлээр бич."
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


def _mock(user: dict, typed: str, lang: str = "mn") -> dict:
    lang = i18n.norm(lang)
    ingredients = [s.strip() for s in typed.replace("،", ",").split(",") if s.strip()] or list(i18n.DEMO_INGREDIENTS[lang])
    lose = user.get("goal") == "lose"
    r1, r2 = (dict(r) for r in i18n.DEMO_RECIPES[lang])
    r1.update(kcal=420 if lose else 560, protein_g=38, time_min=20)
    r2.update(kcal=310, protein_g=22, time_min=10)
    return {"ingredients": ingredients, "recipes": [r1, r2]}
