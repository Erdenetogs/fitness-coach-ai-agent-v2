"""Дүрэмд суурилсан дасгалын төлөвлөгөө ба калорийн тооцоо.
AI түлхүүргүй байсан ч сайт бүрэн ажиллахын тулд эхний төлөвлөгөөг энд гаргана.
Дараа нь агент энэ төлөвлөгөөг хэрэглэгчийн хүсэлтээр өөрчилнө."""
from datetime import date

WEEKDAYS = ["Даваа", "Мягмар", "Лхагва", "Пүрэв", "Баасан", "Бямба", "Ням"]

GOALS = {
    "lose": "Жин хасах",
    "gain": "Булчин нэмэх",
    "fit": "Эрүүл чийрэг байх",
}
LEVELS = {"beginner": "Анхан", "intermediate": "Дунд", "advanced": "Ахисан"}
EQUIPMENT = {"none": "Багажгүй (гэрт)", "dumbbell": "Гантель", "gym": "Фитнес заал"}

# Дасгалын сан: (нэр, icon, төрөл)
LIBRARY = {
    "none": {
        "upper": [("Түлхэлт (push-up)", "fitness_center"), ("Сандал дээр трицепс", "chair"), ("Планк", "horizontal_rule"), ("Пайк түлхэлт", "change_history")],
        "lower": [("Суулт (squat)", "accessibility_new"), ("Лунж", "directions_walk"), ("Гүүр (glute bridge)", "airline_seat_flat"), ("Тугалын өргөлт", "height")],
        "cardio": [("Үсрэлт (jumping jack)", "sprint"), ("Уулчин (mountain climber)", "landscape"), ("Бёрпи", "bolt"), ("Хурдан алхалт", "directions_walk")],
    },
    "dumbbell": {
        "upper": [("Гантель цээжний түлхэлт", "fitness_center"), ("Гантель мөрний түлхэлт", "fitness_center"), ("Нэг гартай татлага", "rowing"), ("Бицепс нугалалт", "sports_gymnastics")],
        "lower": [("Гоблет суулт", "accessibility_new"), ("Румын татлага", "fitness_center"), ("Гантельтай лунж", "directions_walk"), ("Гүүр", "airline_seat_flat")],
        "cardio": [("Гантель свинг", "sprint"), ("Үсрэлт", "bolt"), ("Уулчин", "landscape"), ("Хурдан алхалт", "directions_walk")],
    },
    "gym": {
        "upper": [("Штанга цээжний түлхэлт", "fitness_center"), ("Lat pulldown", "rowing"), ("Мөрний түлхэлт", "fitness_center"), ("Кабель трицепс", "sports_gymnastics")],
        "lower": [("Штанга суулт", "accessibility_new"), ("Leg press", "airline_seat_recline_extra"), ("Румын татлага", "fitness_center"), ("Leg curl", "airline_seat_flat")],
        "cardio": [("Гүйлтийн зам", "directions_run"), ("Дугуй", "directions_bike"), ("Гиребны машин", "rowing"), ("Шат", "stairs")],
    },
}

SPLITS = {
    2: ["full", "full"],
    3: ["upper", "lower", "cardio"],
    4: ["upper", "lower", "cardio", "full"],
    5: ["upper", "lower", "cardio", "upper", "lower"],
    6: ["upper", "lower", "cardio", "upper", "lower", "cardio"],
}
SPREAD = {
    2: [0, 3], 3: [0, 2, 4], 4: [0, 1, 3, 4], 5: [0, 1, 2, 3, 4], 6: [0, 1, 2, 3, 4, 5],
}
FOCUS_NAMES = {"upper": "Дээд бие", "lower": "Доод бие", "cardio": "Кардио", "full": "Бүтэн бие"}


def _sets_reps(level: str, goal: str) -> tuple[int, int]:
    sets = {"beginner": 2, "intermediate": 3, "advanced": 4}.get(level, 3)
    reps = {"lose": 15, "gain": 10, "fit": 12}.get(goal, 12)
    return sets, reps


def build_plan(user: dict) -> dict:
    days = max(2, min(6, int(user.get("days_per_week") or 3)))
    lib = LIBRARY.get(user.get("equipment") or "none", LIBRARY["none"])
    sets, reps = _sets_reps(user.get("level"), user.get("goal"))
    cardio_min = {"beginner": 15, "intermediate": 20, "advanced": 30}.get(user.get("level"), 20)

    plan = {d: {"focus": "rest", "title": "Амрах өдөр", "exercises": []} for d in WEEKDAYS}
    for idx, focus in zip(SPREAD[days], SPLITS[days]):
        if focus == "full":
            moves = lib["upper"][:2] + lib["lower"][:2]
        else:
            moves = lib[focus]
        exercises = []
        for name, icon in moves:
            if focus == "cardio":
                exercises.append({"name": name, "icon": icon, "duration_min": max(5, cardio_min // 2)})
            else:
                exercises.append({"name": name, "icon": icon, "sets": sets, "reps": reps})
        plan[WEEKDAYS[idx]] = {"focus": focus, "title": FOCUS_NAMES[focus], "exercises": exercises}
    return plan


def today_name() -> str:
    return WEEKDAYS[date.today().weekday()]


def nutrition(user: dict) -> dict:
    """Mifflin-St Jeor томьёогоор өдрийн калори, уураг."""
    w = float(user.get("weight_kg") or 65)
    h = float(user.get("height_cm") or 170)
    a = int(user.get("age") or 22)
    bmr = 10 * w + 6.25 * h - 5 * a + (5 if user.get("gender") == "male" else -161)
    activity = {2: 1.375, 3: 1.45, 4: 1.55, 5: 1.6, 6: 1.725}.get(int(user.get("days_per_week") or 3), 1.45)
    tdee = bmr * activity
    goal = user.get("goal")
    kcal = tdee - 400 if goal == "lose" else tdee + 300 if goal == "gain" else tdee
    protein = w * (2.0 if goal == "gain" else 1.6)
    return {"kcal": int(round(kcal, -1)), "protein_g": int(round(protein)), "tdee": int(round(tdee, -1))}


def bmi(user: dict) -> float:
    h = float(user.get("height_cm") or 170) / 100
    return round(float(user.get("weight_kg") or 65) / (h * h), 1)
