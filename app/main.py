"""FitCoach — FastAPI сервер.
Асаах:  uvicorn app.main:app --reload   →  http://127.0.0.1:8000
API туршилт:  http://127.0.0.1:8000/docs
"""
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app import db, planner, xp
from app.agent import coach, fridge, llm

BASE = Path(__file__).parent
app = FastAPI(title="FitCoach AI Agent")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
templates.env.globals.update(GOALS=planner.GOALS, LEVELS=planner.LEVELS, EQUIPMENT=planner.EQUIPMENT,
                             WEEKDAYS=planner.WEEKDAYS)

db.init_db()

COOKIE = "fitcoach_uid"


def current_user(request: Request):
    return db.get_user(request.cookies.get(COOKIE))


def page(request: Request, name: str, active: str, **ctx):
    user = ctx.get("user") or current_user(request)
    coach_status = xp.status(user["id"]) if user else None
    return templates.TemplateResponse(request, name, {"active": active, "user": user, "ai_live": llm.is_live(),
                                                      "coach": coach_status, **ctx})


def need_user(request: Request):
    user = current_user(request)
    return user, (None if user else RedirectResponse("/onboarding", status_code=303))


# ======================= Хуудсууд =======================
@app.get("/onboarding")
def onboarding_page(request: Request):
    return page(request, "onboarding.html", "onboarding")


@app.post("/onboarding")
def onboarding_submit(
    name: str = Form(...), age: int = Form(...), gender: str = Form(...),
    height_cm: float = Form(...), weight_kg: float = Form(...), goal: str = Form(...),
    level: str = Form(...), days_per_week: int = Form(...), equipment: str = Form(...),
):
    data = dict(name=name.strip()[:40], age=age, gender=gender, height_cm=height_cm, weight_kg=weight_kg,
                goal=goal, level=level, days_per_week=days_per_week, equipment=equipment)
    uid = db.create_user(data)
    db.save_plan(uid, planner.build_plan(data))
    db.add_message(uid, "assistant",
                   f"Сайн уу, {data['name']}! Би чиний FitCoach. {days_per_week} өдрийн төлөвлөгөөг чинь бэлдлээ. "
                   "Дасгал солих, жингээ бүртгэх, хоолны талаар асуух бол энд бичээрэй.",
                   [{"icon": "edit_calendar", "text": "Долоо хоногийн төлөвлөгөө үүсгэсэн"}])
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie(COOKIE, str(uid), max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax")
    return resp


@app.get("/")
def home(request: Request):
    user, redirect = need_user(request)
    if redirect:
        return redirect
    plan = db.get_plan(user["id"])
    tname = planner.today_name()
    today = plan.get(tname, {"title": "Амрах өдөр", "exercises": []})
    done = db.get_done_today(user["id"])
    weights = db.get_weights(user["id"])
    week_days = [(d, plan.get(d, {}).get("title", "Амрах өдөр"), bool(plan.get(d, {}).get("exercises"))) for d in planner.WEEKDAYS]
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


@app.post("/profile")
def profile_save(
    request: Request, name: str = Form(...), age: int = Form(...), gender: str = Form(...),
    height_cm: float = Form(...), goal: str = Form(...), level: str = Form(...),
    days_per_week: int = Form(...), equipment: str = Form(...), rebuild: str = Form("no"),
):
    user, redirect = need_user(request)
    if redirect:
        return redirect
    data = dict(name=name.strip()[:40], age=age, gender=gender, height_cm=height_cm, goal=goal, level=level,
                days_per_week=days_per_week, equipment=equipment)
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


@app.get("/logout")
def logout():
    resp = RedirectResponse("/onboarding", status_code=303)
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
        return None, JSONResponse({"error": "Эхлээд бүртгүүлнэ үү"}, status_code=401)
    return user, None


@app.post("/api/chat")
def api_chat(body: ChatIn, request: Request):
    user, err = _api_user(request)
    if err:
        return err
    msg = body.message.strip()[:1000]
    if not msg:
        return JSONResponse({"error": "Мессеж хоосон байна"}, status_code=400)
    result = coach.chat(user["id"], msg)
    return {**result, "xp": xp.award(user["id"], "chat", db.today())}


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
            return JSONResponse({"error": "Зураг 5MB-аас бага байх ёстой"}, status_code=400)
        if media not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
            return JSONResponse({"error": "JPG, PNG, WEBP зураг оруулна уу"}, status_code=400)
    if not image and not ingredients.strip():
        return JSONResponse({"error": "Зураг оруулах эсвэл орцоо бичнэ үү"}, status_code=400)
    return fridge.analyze(user["id"], image, media, ingredients.strip())


@app.post("/api/recipes")
def api_save_recipe(body: RecipeIn, request: Request):
    user, err = _api_user(request)
    if err:
        return err
    db.save_recipe(user["id"], body.recipe)
    title = str(body.recipe.get("title", ""))[:80]
    return {"ok": True, "xp": xp.award(user["id"], "meal", f"{db.today()}:{title}")}


@app.post("/api/workout/done")
def api_done(body: DoneIn, request: Request):
    user, err = _api_user(request)
    if err:
        return err
    db.set_exercise_done(user["id"], body.exercise, body.done)
    done = db.get_done_today(user["id"])
    today_plan = db.get_plan(user["id"]).get(planner.today_name(), {})
    names = {e["name"] for e in today_plan.get("exercises", [])}
    gained = xp.award(user["id"], "workout", db.today()) if names and names <= done else None
    return {"ok": True, "done_today": sorted(done), "xp": gained}


@app.post("/api/weight")
def api_weight(body: WeightIn, request: Request):
    user, err = _api_user(request)
    if err:
        return err
    if not 25 <= body.kg <= 300:
        return JSONResponse({"error": "Жин 25–300 кг хооронд байх ёстой"}, status_code=400)
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
    return xp.status(user["id"])


@app.get("/api/status")
def api_status():
    return {"ai_live": llm.is_live(), "model": llm.MODEL}
