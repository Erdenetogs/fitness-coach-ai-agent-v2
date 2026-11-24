"""Хөргөгчний зураг → орц таних → хэрэглэгчийн зорилгод тохирсон жор.

Claude-ийн зураг харах (vision) чадварыг ашиглана. Хариуг заавал тогтсон JSON бүтэцтэй
авахын тулд "submit_recipes" хэрэгслийг заавал дуудуулна (tool_choice)."""
import base64
import re

from app import db, i18n, planner
from app.agent import llm

RECIPE_TOOL = {
    "name": "submit_recipes",
    "description": "Submit the food found in the photo and the suggested recipes, in the user's language.",
    "input_schema": {
        "type": "object",
        "properties": {
            "seen_en": {"type": "array", "items": {"type": "string"}, "maxItems": 15,
                        "description": "First, in English: short names of food items clearly visible (e.g. cauliflower, mushrooms, ground beef)"},
            "ingredients": {"type": "array", "items": {"type": "string"}, "description": "Confidently identified food items, short names (1–3 words), in the OUTPUT LANGUAGE", "maxItems": 15},
            "recipes": {
                "type": "array",
                "minItems": 1, "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "kcal": {"type": "integer", "description": "kcal per serving"},
                        "protein_g": {"type": "integer"},
                        "time_min": {"type": "integer"},
                        "uses": {"type": "array", "items": {"type": "string"}, "description": "Ingredients from the photo it uses"},
                        "extra": {"type": "array", "items": {"type": "string"}, "description": "Extra ingredients to buy"},
                        "steps": {"type": "array", "items": {"type": "string"}},
                        "why": {"type": "string", "description": "One sentence: why it fits the user's goal"},
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


# Хэл бүрийн жишээ — промпт дахь жишээ монгол байвал AI хариуг монголоор бичдэг байсан тул хэлээр нь сольдог.
_EXAMPLES = {
    "mn": ('"Өндөг", "Банана", "Кетчуп", "Бяслаг"', '"Өндөг (6)"', '"Сонгино / сармис"',
           "cauliflower = Цэцэгт байцаа, mushroom = Мөөг, ground meat = Татсан мах, sausage = Хиам, "
           "condensed milk = Өтгөрүүлсэн сүү, butter = Цөцгийн тос"),
    "en": ('"Eggs", "Bananas", "Ketchup", "Cheese"', '"Eggs (6)"', '"onion / garlic"',
           "use common English grocery names"),
    "ko": ('"계란", "바나나", "케첩", "치즈"', '"계란 (6)"', '"양파 / 마늘"',
           "cauliflower = 콜리플라워, mushroom = 버섯, ground meat = 다진 고기, sausage = 소시지, "
           "condensed milk = 연유, butter = 버터"),
}


def _prompt(user, n, memories, typed, lang="mn") -> str:
    lang = i18n.norm(lang)
    language = i18n.AI_LANG[lang]
    names, counted, unsure, dictionary = _EXAMPLES[lang]
    goal = i18n.t(f"goal.{user.get('goal') or 'fit'}", "en")
    return (
        f"OUTPUT LANGUAGE: {language}. Write every ingredient name, recipe title, step and explanation in {language} only "
        f"(not Mongolian unless the language is Mongolian, never mixed).\n\n"
        f"User goal: {goal}. Daily target: {n['kcal']} kcal, protein {n['protein_g']} g.\n"
        f"User notes (may be in another language — use them, don't copy their language): {'; '.join(memories) or 'none'}.\n"
        + (f"Ingredients the user typed: {typed}\n" if typed else "")
        + "Identify the food in the photo (or list). Suggest 2–3 recipes a student can cook in 30 minutes, mainly using them. "
          "Skip anything the user is allergic to or dislikes. Send with submit_recipes.\n"
          "Ingredient rules (ingredients):\n"
          "- Only FOOD usable for cooking. Leave out containers, cups, bags or cans you can't identify.\n"
          f"- Each name short, 1–3 words, e.g. {names}. No colour, package or notes in brackets. "
          f"A count only when you can clearly count it: {counted}.\n"
          f"- If unsure which of two things it is ({unsure}), skip it. Never write 'unclear' or 'maybe'.\n"
          "- No duplicates, at most 15.\n"
          f"- First list them in English in seen_en, then translate each exactly into {language} in ingredients "
          f"({dictionary}). Don't invent words.\n"
          "Give every recipe real kcal, protein and full steps — never 0 or a placeholder.\n"
          f"Reminder: everything in {language}."
    )


def _analyze_live(user, n, memories, image_bytes, media_type, typed, lang="mn") -> dict:
    client = llm.get_client()
    prompt = _prompt(user, n, memories, typed, lang)
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
        if block.input.get("ingredients") and not data["ingredients"]:
            last = ValueError("орц буруу хэлээр ирсэн")  # бүгд шүүгдсэн → дахин оролдоно
            continue
        if data["recipes"] and resp.stop_reason != "max_tokens":  # буруу хэлээр ирвэл шүүгдэж хоосорно → дахин оролдоно
            return data
        last = ValueError("жор дутуу ирсэн")
    raise last


def _good_recipe(r) -> bool:
    if not isinstance(r, dict):
        return False
    text = " ".join(str(r.get(k, "")) for k in ("title", "why")).lower()
    return (bool(str(r.get("title", "")).strip()) and isinstance(r.get("kcal"), int) and r["kcal"] > 0
            and isinstance(r.get("steps"), list) and len(r["steps"]) > 0 and "placeholder" not in text)


_CYR = re.compile(r"[А-Яа-яЁёӨөҮү]")
_HAN = re.compile(r"[가-힣]")


def _wrong_script(text: str, lang: str) -> bool:
    """Сонгосон хэлэнд байх ёсгүй үсэг байгаа эсэх (жишээ нь солонгос хэл дээр кирилл)."""
    if lang == "ko":
        return bool(_CYR.search(text))
    if lang == "en":
        return bool(_CYR.search(text) or _HAN.search(text))
    return bool(_HAN.search(text))


def clean_result(data: dict, lang: str = "mn") -> dict:
    """AI-ийн хариуг цэгцэлнэ: эвдэрсэн жорыг хасаж, давхардсан орцыг арилгана.
    Монгол/солонгос хэл дээр зөвхөн латин үсгээр бичигдсэн (орчуулагдаагүй, "Cargot" гэх мэт) орцыг хасна."""
    seen, ingredients = set(), []
    for x in data.get("ingredients") or []:
        x = str(x).strip()
        key = x.lower()
        if lang != "en" and x and not re.search(r"[^\W\d_a-zA-Z]", x):
            continue  # латин үсэг л байна — орчуулагдаагүй
        if _wrong_script(x, lang):
            continue  # өөр хэлээр бичигдсэн
        if x and key not in seen:
            seen.add(key)
            ingredients.append(x)
    recipes = [r for r in (data.get("recipes") or [])
               if _good_recipe(r) and not _wrong_script(f"{r.get('title', '')} {r.get('why', '')}", lang)]
    return {"ingredients": ingredients[:15], "recipes": recipes[:3]}


def _mock(user: dict, typed: str, lang: str = "mn") -> dict:
    lang = i18n.norm(lang)
    ingredients = [s.strip() for s in typed.replace("،", ",").split(",") if s.strip()] or list(i18n.DEMO_INGREDIENTS[lang])
    lose = user.get("goal") == "lose"
    r1, r2 = (dict(r) for r in i18n.DEMO_RECIPES[lang])
    r1.update(kcal=420 if lose else 560, protein_g=38, time_min=20)
    r2.update(kcal=310, protein_g=22, time_min=10)
    return {"ingredients": ingredients, "recipes": [r1, r2]}
