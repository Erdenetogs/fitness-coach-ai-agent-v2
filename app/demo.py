"""Демо хэрэглэгч — илтгэл болон туршилтад зориулсан.

Render-ийн үнэгүй сервер унтах/дахин асах бүрт өгөгдлийн сан хоосордог. Тиймээс
бүртгэлийн хуудасны "Демо хэрэглэгчээр үзэх" товч дарах бүрт 3 долоо хоногийн түүхтэй
шинэ хэрэглэгч үүсгэнэ: жингийн өөрчлөлт, хийсэн дасгал, XP/level, санах ой, чат, жор.
"""
import json
from datetime import date, timedelta

from app import db, planner, xp

DAYS = 21

PROFILE = dict(age=21, gender="female", height_cm=165.0, goal="lose", level="beginner",
               days_per_week=4, equipment="none")
START_KG, END_KG = 64.0, 61.8

NAME = {"mn": "Демо оюутан", "en": "Demo student", "ko": "데모 학생"}

MEMORIES = {
    "mn": ["Зүүн өвдөг заримдаа өвддөг — үсрэлттэй дасгалаас зайлсхийх", "Сүү уухаар гэдэс өвддөг",
           "Даваа, Лхагва гарагт орой 6 цагаас хойш л завтай"],
    "en": ["Left knee sometimes hurts — avoid jumping exercises", "Milk upsets their stomach",
           "Free only after 6 pm on Mondays and Wednesdays"],
    "ko": ["왼쪽 무릎이 가끔 아픔 — 점프 운동 피하기", "우유를 마시면 배가 아픔",
           "월요일, 수요일은 저녁 6시 이후에만 시간 있음"],
}

CHAT = {
    "mn": [
        ("user", "Зүүн өвдөг өвдөөд байна, өнөөдөр гүйж болох уу?", None),
        ("assistant", "Өвдөгний тухай санах ойдоо хадгаллаа. Өнөөдөр гүйлтийн оронд дугуй эсвэл хурдан алхалт хийе — "
                      "өвдөгт ачаалал бага. Кардио өдрийн дасгалыг тэгж өөрчиллөө. Өвдөлт 2–3 хоног үргэлжилбэл эмчид үзүүлээрэй.",
         [("bookmark_added", "Санах ойд хадгалсан: Зүүн өвдөг заримдаа өвддөг"),
          ("calendar_month", "Дасгалын төлөвлөгөөг шалгасан"), ("edit_calendar", "Кардио өдрийг өөрчилсөн")]),
        ("user", "Энэ долоо хоногийн явц хэр байна?", None),
        ("assistant", "Сүүлийн 7 хоногт 4 өдөр дасгал хийж, жин эхлэлээс **−2.2 кг** буурсан байна. "
                      "Хэмнэл маш сайн — 5 өдөр дараалан идэвхтэй байна!",
         [("history", "Дасгалын түүхийг шалгасан"), ("monitoring", "Жингийн явцыг шалгасан")]),
    ],
    "en": [
        ("user", "My left knee hurts, can I run today?", None),
        ("assistant", "I've saved the knee note to memory. Let's swap running for cycling or a brisk walk today — "
                      "much easier on the knee. I've updated your cardio day. If it still hurts in 2–3 days, see a doctor.",
         [("bookmark_added", "Saved to memory: Left knee sometimes hurts"),
          ("calendar_month", "Checked the workout plan"), ("edit_calendar", "Changed the cardio day")]),
        ("user", "How's my progress this week?", None),
        ("assistant", "You trained 4 days in the last week and you're **−2.2 kg** from your start. "
                      "Great rhythm — a 5-day streak!",
         [("history", "Checked workout history"), ("monitoring", "Checked weight progress")]),
    ],
    "ko": [
        ("user", "왼쪽 무릎이 아픈데 오늘 달려도 될까요?", None),
        ("assistant", "무릎 상태를 기억해 둘게요. 오늘은 달리기 대신 자전거나 빠르게 걷기로 바꿔요 — 무릎 부담이 적어요. "
                      "유산소 날 운동을 바꿨어요. 2–3일 넘게 아프면 병원에 가 보세요.",
         [("bookmark_added", "기억에 저장: 왼쪽 무릎이 가끔 아픔"),
          ("calendar_month", "운동 계획 확인"), ("edit_calendar", "유산소 날 변경")]),
        ("user", "이번 주 진행 상황 어때요?", None),
        ("assistant", "지난 7일 동안 4일 운동했고 시작보다 **−2.2 kg** 줄었어요. 리듬이 아주 좋아요 — 5일 연속이에요!",
         [("history", "운동 기록 확인"), ("monitoring", "체중 변화 확인")]),
    ],
}

RECIPES = [
    {"title": "Тахиатай брокколи шарсан будаа", "kcal": 420, "protein_g": 38, "time_min": 20,
     "uses": ["Тахианы мах", "Брокколи", "Будаа", "Өндөг"], "extra": ["Шар буурцгийн сүмс"],
     "steps": ["Тахианы махыг жижиглэн 6 мин шарна", "Брокколи нэмж 3 мин хутгана", "Будаа, өндөг нэмээд амтлана"],
     "why": "Уураг ихтэй, жин хасах зорилгод тохирсон."},
    {"title": "Ногоотой өндөгний омлет", "kcal": 310, "protein_g": 22, "time_min": 10,
     "uses": ["Өндөг", "Сонгино", "Вандуй"], "extra": [],
     "steps": ["3 өндгийг хутгана", "Ногоогоо 2 мин шарна", "Өндгөө хийж таглаад 4 мин болгоно"],
     "why": "Хурдан, хямд, сүүгүй."},
]


def create(lang: str = "mn") -> tuple[int, str]:
    """3 долоо хоногийн түүхтэй демо хэрэглэгч үүсгээд (id, token) буцаана."""
    lang = lang if lang in NAME else "mn"
    today = date.today()
    start = today - timedelta(days=DAYS - 1)
    data = {**PROFILE, "name": NAME[lang], "weight_kg": END_KG}
    uid, token = db.create_user(data)
    plan = planner.build_plan(data)
    db.save_plan(uid, plan)

    rows_w, rows_log, rows_xp = [], [], []
    for i in range(DAYS):
        d = start + timedelta(days=i)
        ds = d.isoformat()
        if i % 3 == 0 or i == DAYS - 1:  # 3 хоног тутам жин
            kg = round(START_KG + (END_KG - START_KG) * i / (DAYS - 1) + (0.2 if i % 2 else -0.1), 1)
            rows_w.append((uid, ds, END_KG if i == DAYS - 1 else kg))
        if d == today:
            continue  # өнөөдрийн дасгалыг хэрэглэгч өөрөө тэмдэглэнэ
        exercises = plan[planner.WEEKDAYS[d.weekday()]]["exercises"]
        skipped = i in (3, 10)  # бодит харагдуулахын тулд 2 өдөр алгассан
        if exercises and not skipped:
            rows_log += [(uid, ds, e["name"], 1) for e in exercises]
            rows_xp.append((uid, ds, "workout", xp.XP["workout"], ds))
        if i % 2 == 0 or i >= DAYS - 6:  # сүүлийн өдрүүдэд өдөр бүр чатласан → streak
            rows_xp.append((uid, ds, "chat", xp.XP["chat"], ds))
    for k, r in enumerate(RECIPES):
        ds = (today - timedelta(days=5 - 3 * k)).isoformat()
        rows_xp.append((uid, ds, "meal", xp.XP["meal"], f"{ds}:{r['title']}"))

    with db.conn() as c:
        c.execute("DELETE FROM weights WHERE user_id=?", (uid,))
        c.executemany("INSERT INTO weights (user_id, day, kg) VALUES (?,?,?)", rows_w)
        c.executemany("INSERT OR IGNORE INTO workout_logs (user_id, day, exercise, done) VALUES (?,?,?,?)", rows_log)
        c.executemany("INSERT OR IGNORE INTO xp_events (user_id, day, kind, amount, key) VALUES (?,?,?,?,?)", rows_xp)
        c.executemany("INSERT INTO recipes (user_id, recipe_json, created_at) VALUES (?,?,?)",
                      [(uid, json.dumps(r, ensure_ascii=False), db.now()) for r in RECIPES])

    for text in MEMORIES[lang]:
        db.add_memory(uid, text)
    for role, content, steps in CHAT[lang]:
        db.add_message(uid, role, content, [{"icon": i, "text": t} for i, t in steps] if steps else None)
    return uid, token
