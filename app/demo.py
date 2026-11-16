"""Демо хэрэглэгч — илтгэл болон туршилтад зориулсан.

Render-ийн үнэгүй сервер унтах/дахин асах бүрт өгөгдлийн сан хоосордог. Тиймээс
бүртгэлийн хуудасны "Демо хэрэглэгчээр үзэх" товч дарах бүрт 3 долоо хоногийн түүхтэй
шинэ хэрэглэгч үүсгэнэ: жингийн өөрчлөлт, хийсэн дасгал, XP/level, санах ой, чат, жор.

Анхаар: урьдчилан бичсэн чат өгөгдөлтэйгээ яг таарах ёстой. Жинхэнэ AI хэрэгслээр шалгахдаа
зөрүү олбол "өмнө нь буруу хэлсэн" гэж хариулдаг. Тиймээс:
  - чатад "кардио өдрийг богиносгосон" гэсэн тул төлөвлөгөөг үнэхээр өөрчилнө (SHORT_CARDIO)
  - явцын тоо (хэдэн өдөр, хэдэн кг, streak)-г үүсгэсэн өгөгдлөөс тооцож чатад бичнэ
"""
import json
from datetime import timedelta

from app import db, i18n, planner, xp

DAYS = 21

PROFILE = dict(age=21, gender="female", height_cm=165.0, goal="lose", level="beginner",
               days_per_week=4, equipment="none")
START_KG, END_KG = 64.0, 61.8

NAME = {"mn": "Демо оюутан", "en": "Demo student", "ko": "데모 학생"}

MEMORIES = {
    "mn": ["Шалгалтын үеэр завгүй — дасгалыг 20 минутад багтаах", "Тахианы мах, өндөг дуртай",
           "Даваа, Лхагва гарагт орой 6 цагаас хойш л завтай"],
    "en": ["Busy during exams — keep workouts to 20 minutes", "Likes chicken and eggs",
           "Free only after 6 pm on Mondays and Wednesdays"],
    "ko": ["시험 기간에는 바쁨 — 운동은 20분 이내로", "닭고기와 달걀을 좋아함",
           "월요일, 수요일은 저녁 6시 이후에만 시간 있음"],
}

# "Шалгалттай, завгүй" гэсэн ярианы дараа кардио өдөр 20 минутад багтахаар богиноссон
SHORT_CARDIO = [
    {"name": "Үсрэлт (jumping jack)", "icon": "sprint", "sets": 2, "reps": 15},
    {"name": "Уулчин (mountain climber)", "icon": "landscape", "sets": 2, "reps": 15},
    {"name": "Хурдан алхалт", "icon": "directions_walk", "duration_min": 10},
]

# {n} — сүүлийн 7 хоногт дасгал хийсэн өдөр, {ch} — эхлэлээс хэдэн кг, {s} — дараалсан идэвхтэй өдөр
CHAT = {
    "mn": [
        ("user", "Энэ долоо хоног шалгалттай, их завгүй байна. Кардио дасгалаа 20 минутад багтаагаад өгөөч.", None),
        ("assistant", "Шалгалтын үеэр завгүй гэдгийг санах ойдоо хадгаллаа. Кардио өдрийг 20 минутад багтаахаар богиносгосон: "
                      "үсрэлт 2×15, уулчин 2×15, хурдан алхалт 10 минут. Богино ч гэсэн тогтмол хийх нь чухал. "
                      "Шалгалтдаа амжилт хүсье!",
         [("bookmark_added", "Санах ойд хадгалсан: Шалгалтын үеэр завгүй"),
          ("calendar_month", "Дасгалын төлөвлөгөөг шалгасан"), ("edit_calendar", "{day} гарагийн дасгалыг өөрчилсөн")]),
        ("user", "Энэ долоо хоногийн явц хэр байна?", None),
        ("assistant", "Сүүлийн 7 хоногт {n} өдөр дасгал хийж, жин эхлэлээс **{ch} кг** буурсан байна. "
                      "Хэмнэл маш сайн — {s} өдөр дараалан идэвхтэй байна!",
         [("history", "Дасгалын түүхийг шалгасан"), ("monitoring", "Жингийн явцыг шалгасан")]),
    ],
    "en": [
        ("user", "I have exams this week and I'm really busy. Can you fit my cardio day into 20 minutes?", None),
        ("assistant", "I've saved that you're busy during exams. Your cardio day now fits in 20 minutes: "
                      "jumping jacks 2×15, mountain climbers 2×15 and a 10-minute brisk walk. Short but regular beats skipping. "
                      "Good luck with your exams!",
         [("bookmark_added", "Saved to memory: Busy during exams"),
          ("calendar_month", "Checked your workout plan"), ("edit_calendar", "Changed {day}'s workout")]),
        ("user", "How's my progress this week?", None),
        ("assistant", "You trained {n} days in the last week and you're **{ch} kg** from your start. "
                      "Great rhythm: you've been active {s} days in a row!",
         [("history", "Checked your workout history"), ("monitoring", "Checked your weight trend")]),
    ],
    "ko": [
        ("user", "이번 주 시험이라 너무 바빠요. 유산소 운동을 20분 안에 끝나게 해 줄래요?", None),
        ("assistant", "시험 기간에 바쁘다는 걸 기억해 둘게요. 유산소 날을 20분으로 줄였어요: "
                      "점핑 잭 2×15, 마운틴 클라이머 2×15, 빠르게 걷기 10분. 짧아도 꾸준히 하는 게 중요해요. 시험 잘 보세요!",
         [("bookmark_added", "기억에 저장: 시험 기간에 바쁨"),
          ("calendar_month", "운동 계획 확인"), ("edit_calendar", "{day} 운동 변경")]),
        ("user", "이번 주 진행 상황 어때요?", None),
        ("assistant", "지난 7일 동안 {n}일 운동했고 시작보다 **{ch} kg** 줄었어요. 리듬이 아주 좋아요 — {s}일 연속이에요!",
         [("history", "운동 기록 확인"), ("monitoring", "체중 변화 확인")]),
    ],
}

# Жорын тоон мэдээлэл. Нэр, орц, алхам нь хэлээрээ i18n.DEMO_RECIPES-ээс ирнэ.
RECIPE_NUMBERS = [
    {"kcal": 420, "protein_g": 38, "time_min": 20},
    {"kcal": 310, "protein_g": 22, "time_min": 10},
]


def _weight(i: int) -> float:
    """i-р өдрийн жин: эхэнд яг START_KG, төгсгөлд яг END_KG, дунд нь бага зэрэг хэлбэлзэлтэй."""
    if i == 0:
        return START_KG
    if i == DAYS - 1:
        return END_KG
    return round(START_KG + (END_KG - START_KG) * i / (DAYS - 1) + (0.2 if i % 2 else -0.1), 1)


def create(lang: str = "mn") -> tuple[int, str]:
    """3 долоо хоногийн түүхтэй демо хэрэглэгч үүсгээд (id, token) буцаана."""
    lang = lang if lang in NAME else "mn"
    db.delete_old_demo_users()
    today = db.local_date()
    start = today - timedelta(days=DAYS - 1)
    data = {**PROFILE, "name": NAME[lang], "weight_kg": END_KG, "is_demo": True}
    uid, token = db.create_user(data)

    # Өнгөрсөн дасгалууд анхны төлөвлөгөөгөөр хийгдсэн; "завгүй" ярианаас хойш кардио өдөр богиноссон.
    base_plan = planner.build_plan(data)
    cardio_day = next(d for d in planner.WEEKDAYS if base_plan[d]["focus"] == "cardio")
    plan = {**base_plan, cardio_day: {**base_plan[cardio_day], "exercises": SHORT_CARDIO}}
    db.save_plan(uid, plan)

    rows_w, rows_log, rows_xp = [], [], []
    for i in range(DAYS):
        d = start + timedelta(days=i)
        ds = d.isoformat()
        if i % 3 == 0 or i == DAYS - 1:  # 3 хоног тутам жин
            rows_w.append((uid, ds, _weight(i)))
        if d == today:
            continue  # өнөөдрийн дасгалыг хэрэглэгч өөрөө тэмдэглэнэ
        exercises = base_plan[planner.WEEKDAYS[d.weekday()]]["exercises"]
        skipped = i in (3, 10)  # бодит харагдуулахын тулд 2 өдөр алгассан
        if exercises and not skipped:
            rows_log += [(uid, ds, e["name"], 1) for e in exercises]
            rows_xp.append((uid, ds, "workout", xp.XP["workout"], ds))
        if i % 2 == 0 or i >= DAYS - 6:  # сүүлийн өдрүүдэд өдөр бүр чатласан → streak
            rows_xp.append((uid, ds, "chat", xp.XP["chat"], ds))

    recipes = [{**r, **n} for r, n in zip(i18n.DEMO_RECIPES[lang], RECIPE_NUMBERS)]
    for k, r in enumerate(recipes):
        ds = (today - timedelta(days=5 - 3 * k)).isoformat()
        rows_xp.append((uid, ds, "meal", xp.XP["meal"], f"{ds}:{r['title']}"))

    with db.conn() as c:
        c.execute("DELETE FROM weights WHERE user_id=?", (uid,))
        c.executemany("INSERT INTO weights (user_id, day, kg) VALUES (?,?,?)", rows_w)
        c.executemany("INSERT INTO workout_logs (user_id, day, exercise, done) VALUES (?,?,?,?) ON CONFLICT DO NOTHING", rows_log)
        c.executemany("INSERT INTO xp_events (user_id, day, kind, amount, key) VALUES (?,?,?,?,?) ON CONFLICT DO NOTHING", rows_xp)
        c.executemany("INSERT INTO recipes (user_id, recipe_json, created_at) VALUES (?,?,?)",
                      [(uid, json.dumps(r, ensure_ascii=False), db.now()) for r in recipes])

    for text in MEMORIES[lang]:
        db.add_memory(uid, text)

    # Чатад бичих тоонуудыг яг энэ өгөгдлөөс тооцно — AI хэрэгслээр шалгахад таарна.
    week_ago = (today - timedelta(days=7)).isoformat()
    facts = {
        "n": len({r[1] for r in rows_log if r[1] >= week_ago}),
        "ch": f"{END_KG - START_KG:+.1f}".replace("-", "−"),
        "s": xp.streak(uid),
        "day": i18n.weekday(cardio_day, lang),
    }
    for role, content, steps in CHAT[lang]:
        db.add_message(uid, role, content.format(**facts),
                       [{"icon": i, "text": t.format(**facts)} for i, t in steps] if steps else None)
    return uid, token
