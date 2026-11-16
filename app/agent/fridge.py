"""Хөргөгчний зураг → орц таних → хэрэглэгчийн зорилгод тохирсон жор.

Claude-ийн зураг харах (vision) чадварыг ашиглана. Хариуг заавал тогтсон JSON бүтэцтэй
авахын тулд "submit_recipes" хэрэгслийг заавал дуудуулна (tool_choice)."""
import base64
import re

from app import db, i18n, planner
from app.agent import llm

RECIPE_TOOL = {
    "name": "submit_recipes",
    "description": "Зурагнаас олсон орцууд болон санал болгох жоруудыг илгээнэ.",
    "input_schema": {
        "type": "object",
        "properties": {
            "seen_en": {"type": "array", "items": {"type": "string"}, "maxItems": 15,
                        "description": "First, in English: short names of food items clearly visible (e.g. cauliflower, mushrooms, ground beef)"},
            "ingredients": {"type": "array", "items": {"type": "string"}, "description": "Итгэлтэй танигдсан хүнсний орцууд — богино нэр (1–3 үг), тайлбаргүй", "maxItems": 15},
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
        "required": ["seen_en", "ingredients", "recipes"],
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
          "Орцыг таних дүрэм (ingredients):\n"
          "- Зөвхөн хоол хийхэд хэрэглэж болох ХҮНСНИЙ зүйл. Юу болох нь танигдахгүй сав, аяга, уут, лааз бол бүү оруул.\n"
          "- Нэр бүр богино: 1–3 үг, жишээ нь \"Өндөг\", \"Банана\", \"Кетчуп\", \"Бяслаг\". Хаалтанд өнгө, сав, "
          "тайлбар бүү бич. Тоог зөвхөн тодорхой тоолж болох үед \"Өндөг (6)\" гэж бич.\n"
          "- Хоёр зүйлийн аль нь болохыг мэдэхгүй бол (\"Сонгино / сармис\" гэх мэт) бүү бич — алгас. "
          "\"Тодорхойгүй\", \"таамаглал\" гэсэн үгтэй орц огт бүү бич.\n"
          "- Нэг зүйлийг давтахгүй, хамгийн ихдээ 15 орц.\n"
          "- Эхлээд seen_en-д англиар тань, дараа нь ingredients-д түүнийгээ ЯГ орчуул (зөв, түгээмэл нэрээр: "
          "cauliflower = Цэцэгт байцаа, mushroom = Мөөг, ground meat = Татсан мах, sausage = Хиам, "
          "condensed milk = Өтгөрүүлсэн сүү, butter = Цөцгийн тос). Шинэ үг бүү зохио.\n"
          "Жор бүрд бодит калори, уураг, алхмуудыг бүрэн бич — 0 эсвэл placeholder бүү бич.\n"
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
    last = None
    for _ in range(2):  # дутуу/эвдэрсэн хариу ирвэл нэг удаа дахин оролдоно
        resp = client.messages.create(
            model=llm.MODEL,
            max_tokens=4096,  # монгол текст олон токен авдаг — 2048-д 3 жор тасарч байсан
            tools=[RECIPE_TOOL],
            tool_choice={"type": "tool", "name": "submit_recipes"},
            messages=[{"role": "user", "content": content}],
        )
        block = next((b for b in resp.content if b.type == "tool_use"), None)
        if block is None:
            last = ValueError("submit_recipes дуудагдсангүй")
            continue
        data = clean_result(block.input, i18n.norm(lang))
        if data["recipes"] and resp.stop_reason != "max_tokens":
            return data
        last = ValueError("жор дутуу ирсэн")
    raise last


def _good_recipe(r) -> bool:
    if not isinstance(r, dict):
        return False
    text = " ".join(str(r.get(k, "")) for k in ("title", "why")).lower()
    return (bool(str(r.get("title", "")).strip()) and isinstance(r.get("kcal"), int) and r["kcal"] > 0
            and isinstance(r.get("steps"), list) and len(r["steps"]) > 0 and "placeholder" not in text)


def clean_result(data: dict, lang: str = "mn") -> dict:
    """AI-ийн хариуг цэгцэлнэ: эвдэрсэн жорыг хасаж, давхардсан орцыг арилгана.
    Монгол/солонгос хэл дээр зөвхөн латин үсгээр бичигдсэн (орчуулагдаагүй, "Cargot" гэх мэт) орцыг хасна."""
    seen, ingredients = set(), []
    for x in data.get("ingredients") or []:
        x = str(x).strip()
        key = x.lower()
        if lang != "en" and x and not re.search(r"[^\W\d_a-zA-Z]", x):
            continue  # латин үсэг л байна — орчуулагдаагүй
        if x and key not in seen:
            seen.add(key)
            ingredients.append(x)
    recipes = [r for r in (data.get("recipes") or []) if _good_recipe(r)]
    return {"ingredients": ingredients[:15], "recipes": recipes[:3]}


def _mock(user: dict, typed: str, lang: str = "mn") -> dict:
    lang = i18n.norm(lang)
    ingredients = [s.strip() for s in typed.replace("،", ",").split(",") if s.strip()] or list(i18n.DEMO_INGREDIENTS[lang])
    lose = user.get("goal") == "lose"
    r1, r2 = (dict(r) for r in i18n.DEMO_RECIPES[lang])
    r1.update(kcal=420 if lose else 560, protein_g=38, time_min=20)
    r2.update(kcal=310, protein_g=22, time_min=10)
    return {"ingredients": ingredients, "recipes": [r1, r2]}
