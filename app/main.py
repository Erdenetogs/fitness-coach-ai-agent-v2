"""FitCoach — FastAPI сервер.
Асаах:  uvicorn app.main:app --reload   →  http://127.0.0.1:8000
API туршилт:  http://127.0.0.1:8000/docs
"""
import hashlib
import os
import re
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import json

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
from markupsafe import Markup, escape
from pydantic import BaseModel

from app import auth, db, demo, guide, i18n, mascot, planner, xp
from app.agent import coach, fridge, llm

BASE = Path(__file__).parent
app = FastAPI(title="FitCoach AI Agent")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


def _static_version() -> str:
    """static/ доторх файлуудын агуулгаас гаргасан богино hash.
    CSS/JS-ийн холбоос дээр ?v=... болж залгагдана. Файл өөрчлөгдөхөд холбоос өөрчлөгдөж,
    браузер хуучин кэшээ биш шинэ файлыг татна (deploy-ийн дараа "formatReply is not defined" гарахгүй)."""
    h = hashlib.sha256()
    for f in sorted((BASE / "static").rglob("*")):
        if f.is_file():
            h.update(f.read_bytes())
    return h.hexdigest()[:8]


STATIC_V = _static_version()


def _md(text) -> Markup:
    """AI хариуны **тод** бичгийг HTML болгоно. Эхлээд escape хийдэг тул аюулгүй."""
    safe = str(escape(text or ""))
    return Markup(re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe))


templates.env.filters["md"] = _md
templates.env.globals.update(GOALS=planner.GOALS, LEVELS=planner.LEVELS, EQUIPMENT=planner.EQUIPMENT,
                             WEEKDAYS=planner.WEEKDAYS, LANGS=i18n.LANGS, LANG_SHORT=i18n.SHORT,
                             STATIC_V=STATIC_V)


# ---- Template-д хэрэглэх орчуулгын функцууд (хуудасны хэлийг context-оос авна) ----
@pass_context
def _t(ctx, key, **kw):
    return i18n.t(key, ctx.get("lang", i18n.DEFAULT), **kw)


@pass_context
def _wd(ctx, day, short=False):
    return i18n.weekday(day, ctx.get("lang", i18n.DEFAULT), short)


@pass_context
def _title(ctx, day):
    return i18n.day_title(day, ctx.get("lang", i18n.DEFAULT))


@pass_context
def _ex(ctx, name):
    return i18n.exercise(name, ctx.get("lang", i18n.DEFAULT))


@pass_context
def _guide(ctx, name):
    return guide.get(name, ctx.get("lang", i18n.DEFAULT))


templates.env.globals.update(t=_t, wd=_wd, day_title=_title, ex=_ex, guide=_guide, mascot=mascot.svg)

db.init_db()

COOKIE = "fitcoach_token"

# Нэг хэрэглэгч өдөрт хэдэн удаа AI дуудаж болох (API-ийн зардлыг хамгаална). Render-ийн Environment-д өөрчилж болно.
LIMITS = {"chat": int(os.getenv("CHAT_DAILY_LIMIT", "50")), "fridge": int(os.getenv("FRIDGE_DAILY_LIMIT", "10"))}


def current_user(request: Request):
    return db.get_user_by_token(request.cookies.get(COOKIE))


def validate_profile(name: str, age: int, gender: str, height_cm: float, goal: str, level: str,
                     days_per_week: int, equipment: str, weight_kg: float | None = None, lang: str = "mn") -> dict:
    """Формын утгыг серверт дахин шалгана (browser-ийн min/max-ийг тойрч илгээж болдог)."""
    name = name.strip()[:40]
    if not name:
        raise HTTPException(400, i18n.t("err.name", lang))
    if (gender not in ("male", "female") or goal not in planner.GOALS
            or level not in planner.LEVELS or equipment not in planner.EQUIPMENT):
        raise HTTPException(400, i18n.t("err.choice", lang))
    if not (14 <= age <= 80 and 120 <= height_cm <= 230 and 2 <= days_per_week <= 6):
        raise HTTPException(400, i18n.t("err.ranges", lang))
    data = dict(name=name, age=age, gender=gender, height_cm=height_cm, goal=goal, level=level,
                days_per_week=days_per_week, equipment=equipment)
    if weight_kg is not None:
        if not 30 <= weight_kg <= 250:
            raise HTTPException(400, i18n.t("err.weight_form", lang))
        data["weight_kg"] = weight_kg
    return data


def page(request: Request, name: str, active: str, status_code: int = 200, **ctx):
    user = ctx.get("user") or current_user(request)
    lang = i18n.from_request(request)
    coach_status = xp.status(user["id"], lang) if user else None
    return templates.TemplateResponse(request, name, {"active": active, "user": user, "ai_live": llm.is_live(),
                                                      "coach": coach_status, "lang": lang,
                                                      "js_strings": i18n.js_strings(lang), **ctx},
                                      status_code=status_code)


def need_user(request: Request):
    user = current_user(request)
    return user, (None if user else RedirectResponse("/onboarding", status_code=303))


# ======================= Хуудсууд =======================
@app.get("/onboarding")
def onboarding_page(request: Request):
    return page(request, "onboarding.html", "onboarding")


@app.post("/onboarding")
def onboarding_submit(
    request: Request, name: str = Form(...), age: int = Form(...), gender: str = Form(...),
    height_cm: float = Form(...), weight_kg: float = Form(...), goal: str = Form(...),
    level: str = Form(...), days_per_week: int = Form(...), equipment: str = Form(...),
    email: str = Form(...), password: str = Form(...), password2: str = Form(...),
):
    lang = i18n.from_request(request)
    data = validate_profile(name, age, gender, height_cm, goal, level, days_per_week, equipment, weight_kg, lang)
    email = auth.normalize_email(email)
    if not auth.valid_email(email):
        raise HTTPException(400, i18n.t("err.email", lang))
    if not auth.valid_password(password):
        raise HTTPException(400, i18n.t("err.password_short", lang))
    if password != password2:
        raise HTTPException(400, i18n.t("js.pw_mismatch", lang))
    if db.get_user_by_email(email):
        raise HTTPException(409, i18n.t("err.email_taken", lang))
    try:
        uid, token = db.create_user({**data, "email": email, "password_hash": auth.hash_password(password)})
    except db.IntegrityError:  # яг зэрэг ижил имэйлээр бүртгүүлсэн
        raise HTTPException(409, i18n.t("err.email_taken", lang))
    db.save_plan(uid, planner.build_plan(data))
    db.add_message(uid, "assistant", i18n.t("m.greeting", lang, name=data["name"], d=days_per_week),
                   [{"icon": "edit_calendar", "text": i18n.t("step.plan_created", lang)}])
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie(COOKIE, token, max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax")
    return resp


@app.get("/login")
def login_page(request: Request):
    if current_user(request):
        return RedirectResponse("/", status_code=303)
    return page(request, "login.html", "login")


@app.post("/login")
def login_submit(request: Request, email: str = Form(""), password: str = Form("")):
    """Имэйл + нууц үгээр нэвтэрнэ. Аль нь буруу байгааг хэлэхгүй (имэйл бүртгэлтэй эсэхийг таахгүйн тулд)."""
    lang = i18n.from_request(request)
    email = auth.normalize_email(email)
    if auth.locked(email):
        return page(request, "login.html", "login", error=i18n.t("err.too_many", lang), email=email,
                    status_code=429)
    user = db.get_user_by_email(email)
    if not auth.check_login(password, user and user.get("password_hash")):
        auth.record_fail(email)
        return page(request, "login.html", "login", error=i18n.t("err.login", lang), email=email,
                    status_code=401)
    auth.clear_fails(email)
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie(COOKIE, user["token"], max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax")
    return resp


@app.post("/demo")
def demo_login(request: Request):
    """Илтгэл, туршилтад: 3 долоо хоногийн түүхтэй демо хэрэглэгч үүсгээд нэвтрүүлнэ."""
    _, token = demo.create(i18n.from_request(request))
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie(COOKIE, token, max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax")
    return resp


@app.get("/")
def home(request: Request):
    user, redirect = need_user(request)
    if redirect:
        return redirect
    plan = db.get_plan(user["id"])
    tname = planner.today_name()
    today = plan.get(tname, {"focus": "rest", "title": "Амрах өдөр", "exercises": []})
    done = db.get_done_today(user["id"])
    weights = db.get_weights(user["id"])
    week_days = [(d, i18n.day_title(plan.get(d, {}), i18n.from_request(request)), bool(plan.get(d, {}).get("exercises")))
                 for d in planner.WEEKDAYS]
    return page(request, "home.html", "home", user=user, today=today, today_name=tname, done=done,
                nutrition=planner.nutrition(user), weights=weights, memories=db.get_memories(user["id"])[:3],
                week_days=week_days)


@app.get("/workout")
def workout(request: Request):
    user, redirect = need_user(request)
    if redirect:
        return redirect
    return page(request, "workout.html", "workout", plan=db.get_plan(user["id"]), today_name=planner.today_name(),
                done=db.get_done_today(user["id"]))


@app.get("/food")
def food(request: Request):
    user, redirect = need_user(request)
    if redirect:
        return redirect
    return page(request, "food.html", "food", nutrition=planner.nutrition(user), saved=db.get_recipes(user["id"]))


@app.get("/progress")
def progress(request: Request):
    user, redirect = need_user(request)
    if redirect:
        return redirect
    weights = db.get_weights(user["id"])
    history = db.get_workout_history(user["id"], 28)
    change = round(weights[-1]["kg"] - weights[0]["kg"], 1) if len(weights) > 1 else 0
    return page(request, "progress.html", "progress", weights=weights, history=history, change=change,
                bmi=planner.bmi(user))


@app.get("/profile")
def profile(request: Request):
    user, redirect = need_user(request)
    if redirect:
        return redirect
    return page(request, "profile.html", "profile", memories=db.get_memories(user["id"]),
                nutrition=planner.nutrition(user))


def _profile_error(request: Request, user: dict, key: str, status: int, form: str):
    lang = i18n.from_request(request)
    return page(request, "profile.html", "profile", status_code=status, user=user,
                memories=db.get_memories(user["id"]), nutrition=planner.nutrition(user),
                **{f"{form}_error": i18n.t(key, lang)})


@app.post("/profile/password")
def change_password(request: Request, current: str = Form(""), password: str = Form(""), password2: str = Form("")):
    """Одоогийн нууц үгээ оруулж байж шинээр солино. Олон удаа буруу оруулбал нэвтрэхтэй адил түр хаана."""
    user, redirect = need_user(request)
    if redirect:
        return redirect
    if not user.get("password_hash"):  # демо хэрэглэгч
        return _profile_error(request, user, "err.no_password", 400, "pw")
    key = f"pw:{user['id']}"
    if auth.locked(key):
        return _profile_error(request, user, "err.too_many", 429, "pw")
    if not auth.verify_password(current, user["password_hash"]):
        auth.record_fail(key)
        return _profile_error(request, user, "err.current_pw", 401, "pw")
    if not auth.valid_password(password):
        return _profile_error(request, user, "err.password_short", 400, "pw")
    if password != password2:
        return _profile_error(request, user, "js.pw_mismatch", 400, "pw")
    auth.clear_fails(key)
    db.set_password(user["id"], auth.hash_password(password))
    return RedirectResponse("/profile?pw=1", status_code=303)


@app.post("/profile/delete")
def delete_account(request: Request, current: str = Form(""), confirm: str = Form("")):
    """Бүртгэл болон бүх өгөгдлийг бүрмөсөн устгана. Нууц үгтэй бол нууц үгээр баталгаажуулна."""
    user, redirect = need_user(request)
    if redirect:
        return redirect
    if user.get("password_hash"):
        key = f"pw:{user['id']}"
        if auth.locked(key):
            return _profile_error(request, user, "err.too_many", 429, "del")
        if not auth.verify_password(current, user["password_hash"]):
            auth.record_fail(key)
            return _profile_error(request, user, "err.current_pw", 401, "del")
    elif confirm != "yes":
        return _profile_error(request, user, "err.choice", 400, "del")
    db.delete_user(user["id"])
    resp = RedirectResponse("/onboarding?deleted=1", status_code=303)
    resp.delete_cookie(COOKIE)
    return resp


@app.post("/profile")
def profile_save(
    request: Request, name: str = Form(...), age: int = Form(...), gender: str = Form(...),
    height_cm: float = Form(...), goal: str = Form(...), level: str = Form(...),
    days_per_week: int = Form(...), equipment: str = Form(...), rebuild: str = Form("no"),
):
    user, redirect = need_user(request)
    if redirect:
        return redirect
    data = validate_profile(name, age, gender, height_cm, goal, level, days_per_week, equipment,
                            lang=i18n.from_request(request))
    db.update_user(user["id"], data)
    if rebuild == "yes":
        db.save_plan(user["id"], planner.build_plan({**user, **data}))
    return RedirectResponse("/profile?saved=1", status_code=303)


@app.get("/chat")
def chat_page(request: Request):
    user, redirect = need_user(request)
    if redirect:
        return redirect
    return page(request, "chat.html", "chat", messages=db.get_messages(user["id"], 40))


@app.get("/lang/{code}")
def set_language(code: str, next: str = "/"):
    """Хэл солих товч. next нь зөвхөн энэ сайтын зам байна (өөр сайт руу үсрүүлэхгүй)."""
    target = next if next.startswith("/") and not next.startswith("//") and "\\" not in next else "/"
    resp = RedirectResponse(target, status_code=303)
    if code in i18n.LANGS:
        resp.set_cookie(i18n.COOKIE, code, max_age=60 * 60 * 24 * 365, samesite="lax")
    return resp


@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(COOKIE)
    return resp


# ======================= API (JavaScript-аас дуудна) =======================
class ChatIn(BaseModel):
    message: str


class DoneIn(BaseModel):
    exercise: str
    done: bool


class WeightIn(BaseModel):
    kg: float


class RecipeIn(BaseModel):
    recipe: dict


def _api_user(request: Request):
    user = current_user(request)
    if not user:
        return None, JSONResponse({"error": i18n.t("err.register", i18n.from_request(request))}, status_code=401)
    return user, None


def _err(request: Request, key: str, status: int = 400):
    return JSONResponse({"error": i18n.t(key, i18n.from_request(request))}, status_code=status)


@app.post("/api/chat")
def api_chat(body: ChatIn, request: Request):
    user, err = _api_user(request)
    if err:
        return err
    msg = body.message.strip()[:1000]
    if not msg:
        return _err(request, "err.empty_msg")
    lang = i18n.from_request(request)
    if not db.use_quota(user["id"], "chat", LIMITS["chat"]):
        return _err(request, "err.limit", 429)
    result = coach.chat(user["id"], msg, lang)
    return {**result, "xp": xp.award(user["id"], "chat", db.today(), lang)}


@app.post("/api/fridge")
async def api_fridge(request: Request, photo: UploadFile | None = File(None), ingredients: str = Form("")):
    user, err = _api_user(request)
    if err:
        return err
    image, media = None, None
    if photo is not None and photo.filename:
        image = await photo.read()
        media = photo.content_type
        if len(image) > 5 * 1024 * 1024:
            return _err(request, "err.photo_big")
        if media not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
            return _err(request, "err.photo_type")
    if not image and not ingredients.strip():
        return _err(request, "err.need_input")
    if not db.use_quota(user["id"], "fridge", LIMITS["fridge"]):
        return _err(request, "err.limit", 429)
    return fridge.analyze(user["id"], image, media, ingredients.strip(), i18n.from_request(request))


@app.post("/api/recipes")
def api_save_recipe(body: RecipeIn, request: Request):
    user, err = _api_user(request)
    if err:
        return err
    if not body.recipe.get("title") or len(json.dumps(body.recipe, ensure_ascii=False)) > 8000:
        return _err(request, "err.recipe")
    db.save_recipe(user["id"], body.recipe)
    title = str(body.recipe.get("title", ""))[:80]
    return {"ok": True, "xp": xp.award(user["id"], "meal", f"{db.today()}:{title}", i18n.from_request(request))}


@app.post("/api/workout/done")
def api_done(body: DoneIn, request: Request):
    user, err = _api_user(request)
    if err:
        return err
    db.set_exercise_done(user["id"], body.exercise, body.done)
    done = db.get_done_today(user["id"])
    today_plan = db.get_plan(user["id"]).get(planner.today_name(), {})
    names = {e["name"] for e in today_plan.get("exercises", [])}
    lang = i18n.from_request(request)
    gained = xp.award(user["id"], "workout", db.today(), lang) if names and names <= done else None
    return {"ok": True, "done_today": sorted(done), "xp": gained, "cheer": _cheer(user, gained, lang) if gained else None}


def _cheer(user: dict, gained: dict, lang: str) -> dict:
    """Өнөөдрийн дасгалыг дуусгахад дасгалжуулагчийн хэлэх үг. AI дуудахгүй (хурдан, үнэгүй) —
    хэрэглэгчийн бодит өгөгдлөөс (level, streak, 7 хоногийн тоо, зорилго) сонгож бүтээнэ."""
    week = len(db.get_workout_history(user["id"], 6))  # өнөөдрийг оруулаад 7 хоног
    streak = gained.get("streak", 0)
    if gained.get("leveled_up"):
        title, body = i18n.t("cheer.title_level", lang, level=gained["level"]), i18n.t("cheer.level", lang, stage=gained["stage"])
    elif streak >= 3:
        title, body = i18n.t("cheer.title", lang), i18n.t("cheer.streak", lang, n=streak)
    elif week >= 2:
        title, body = i18n.t("cheer.title", lang), i18n.t("cheer.week", lang, n=week)
    else:
        title, body = i18n.t("cheer.title", lang), i18n.t("cheer.first", lang)
    tip = i18n.t(f"cheer.tip_{user.get('goal') if user.get('goal') in ('lose', 'gain') else 'fit'}", lang)
    stats = [f"+{gained['gained']} XP"]
    if streak >= 2:
        stats.append(i18n.t("cheer.stat_streak", lang, n=streak))
    stats.append(i18n.t("cheer.stat_week", lang, n=week))
    # Level ахисан бол шинэ шатны роботыг харуулна (хуудсан дээрх нь хуучин level-ийнх)
    return {"title": title, "text": f"{body} {tip}", "stats": stats, "level": gained["level"],
            "avatar": str(mascot.svg(96, gained["level"], user.get("goal")))}


@app.post("/api/weight")
def api_weight(body: WeightIn, request: Request):
    user, err = _api_user(request)
    if err:
        return err
    if not 25 <= body.kg <= 300:
        return _err(request, "err.weight_api")
    db.add_weight(user["id"], round(body.kg, 1))
    return {"ok": True, "weights": db.get_weights(user["id"])}


@app.get("/api/progress")
def api_progress(request: Request):
    user, err = _api_user(request)
    if err:
        return err
    return {"weights": db.get_weights(user["id"]), "history": db.get_workout_history(user["id"], 28)}


@app.delete("/api/memory/{mid}")
def api_delete_memory(mid: int, request: Request):
    user, err = _api_user(request)
    if err:
        return err
    db.delete_memory(user["id"], mid)
    return {"ok": True}


@app.get("/api/xp")
def api_xp(request: Request):
    user, err = _api_user(request)
    if err:
        return err
    return xp.status(user["id"], i18n.from_request(request))


@app.get("/healthz")
def healthz():
    """Render (deploy) сервер ажиллаж байгааг шалгахад ашиглана."""
    return {"ok": True}


@app.get("/api/status")
def api_status():
    return {"ai_live": llm.is_live(), "model": llm.MODEL, "db": db.DB_KIND}
