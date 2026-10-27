"""SQLite өгөгдлийн сан. Python-д суурилагдсан sqlite3 ашиглана — нэмэлт суулгах зүйлгүй."""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime

DB_PATH = os.getenv("FITCOACH_DB", "fitcoach.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER, gender TEXT, height_cm REAL, weight_kg REAL,
    goal TEXT, level TEXT, days_per_week INTEGER, equipment TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS plans (
    user_id INTEGER PRIMARY KEY, plan_json TEXT NOT NULL, updated_at TEXT
);
CREATE TABLE IF NOT EXISTS weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, day TEXT, kg REAL
);
CREATE TABLE IF NOT EXISTS workout_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, day TEXT, exercise TEXT, done INTEGER,
    UNIQUE(user_id, day, exercise)
);
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, text TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, role TEXT, content TEXT, steps_json TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, recipe_json TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS xp_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, day TEXT, kind TEXT, amount INTEGER, key TEXT,
    UNIQUE(user_id, kind, key)
);
"""


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def today() -> str:
    return date.today().isoformat()


@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_db():
    folder = os.path.dirname(DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with conn() as c:
        c.executescript(SCHEMA)


# ---------- Хэрэглэгч ----------
def create_user(data: dict) -> int:
    with conn() as c:
        cur = c.execute(
            """INSERT INTO users (name, age, gender, height_cm, weight_kg, goal, level,
               days_per_week, equipment, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (data["name"], data["age"], data["gender"], data["height_cm"], data["weight_kg"],
             data["goal"], data["level"], data["days_per_week"], data["equipment"], now()),
        )
        uid = cur.lastrowid
        c.execute("INSERT INTO weights (user_id, day, kg) VALUES (?,?,?)", (uid, today(), data["weight_kg"]))
        return uid


def get_user(uid) -> dict | None:
    if not uid:
        return None
    with conn() as c:
        row = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        return dict(row) if row else None


def update_user(uid: int, data: dict):
    allowed = ["name", "age", "gender", "height_cm", "weight_kg", "goal", "level", "days_per_week", "equipment"]
    fields = {k: v for k, v in data.items() if k in allowed}
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    with conn() as c:
        c.execute(f"UPDATE users SET {sets} WHERE id=?", (*fields.values(), uid))


# ---------- Төлөвлөгөө ----------
def save_plan(uid: int, plan: dict):
    with conn() as c:
        c.execute(
            "INSERT INTO plans (user_id, plan_json, updated_at) VALUES (?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET plan_json=excluded.plan_json, updated_at=excluded.updated_at",
            (uid, json.dumps(plan, ensure_ascii=False), now()),
        )


def get_plan(uid: int) -> dict:
    with conn() as c:
        row = c.execute("SELECT plan_json FROM plans WHERE user_id=?", (uid,)).fetchone()
        return json.loads(row["plan_json"]) if row else {}


# ---------- Жин ----------
def add_weight(uid: int, kg: float, day: str | None = None):
    day = day or today()
    with conn() as c:
        c.execute("DELETE FROM weights WHERE user_id=? AND day=?", (uid, day))
        c.execute("INSERT INTO weights (user_id, day, kg) VALUES (?,?,?)", (uid, day, kg))
        c.execute("UPDATE users SET weight_kg=? WHERE id=?", (kg, uid))


def get_weights(uid: int, limit: int = 60) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT day, kg FROM weights WHERE user_id=? ORDER BY day DESC LIMIT ?", (uid, limit)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]


# ---------- Дасгалын тэмдэглэл ----------
def set_exercise_done(uid: int, exercise: str, done: bool, day: str | None = None):
    day = day or today()
    with conn() as c:
        c.execute(
            "INSERT INTO workout_logs (user_id, day, exercise, done) VALUES (?,?,?,?) "
            "ON CONFLICT(user_id, day, exercise) DO UPDATE SET done=excluded.done",
            (uid, day, exercise, int(done)),
        )


def get_done_today(uid: int) -> set[str]:
    with conn() as c:
        rows = c.execute(
            "SELECT exercise FROM workout_logs WHERE user_id=? AND day=? AND done=1", (uid, today())
        ).fetchall()
        return {r["exercise"] for r in rows}


def get_workout_history(uid: int, days: int = 14) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT day, COUNT(*) AS done_count, GROUP_CONCAT(exercise, ', ') AS exercises "
            "FROM workout_logs WHERE user_id=? AND done=1 AND day >= date('now', ?) "
            "GROUP BY day ORDER BY day",
            (uid, f"-{days} days"),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- Санах ой ----------
def add_memory(uid: int, text: str):
    with conn() as c:
        c.execute("INSERT INTO memories (user_id, text, created_at) VALUES (?,?,?)", (uid, text, now()))


def get_memories(uid: int) -> list[dict]:
    with conn() as c:
        rows = c.execute("SELECT id, text, created_at FROM memories WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
        return [dict(r) for r in rows]


def delete_memory(uid: int, mid: int):
    with conn() as c:
        c.execute("DELETE FROM memories WHERE id=? AND user_id=?", (mid, uid))


# ---------- Чат ----------
def add_message(uid: int, role: str, content: str, steps: list | None = None):
    with conn() as c:
        c.execute(
            "INSERT INTO messages (user_id, role, content, steps_json, created_at) VALUES (?,?,?,?,?)",
            (uid, role, content, json.dumps(steps or [], ensure_ascii=False), now()),
        )


def get_messages(uid: int, limit: int = 30) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT role, content, steps_json FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?", (uid, limit)
        ).fetchall()
    out = []
    for r in reversed(rows):
        out.append({"role": r["role"], "content": r["content"], "agent_steps": json.loads(r["steps_json"] or "[]")})
    return out


# ---------- Жор ----------
def save_recipe(uid: int, recipe: dict):
    with conn() as c:
        c.execute(
            "INSERT INTO recipes (user_id, recipe_json, created_at) VALUES (?,?,?)",
            (uid, json.dumps(recipe, ensure_ascii=False), now()),
        )


def get_recipes(uid: int) -> list[dict]:
    with conn() as c:
        rows = c.execute("SELECT id, recipe_json FROM recipes WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
        return [{"id": r["id"], **json.loads(r["recipe_json"])} for r in rows]


# ---------- XP (оноо) ----------
def award_xp(uid: int, kind: str, amount: int, key: str) -> bool:
    """Нэг (kind, key) хослолд нэг л удаа XP өгнө. Шинээр өгсөн бол True."""
    with conn() as c:
        cur = c.execute(
            "INSERT OR IGNORE INTO xp_events (user_id, day, kind, amount, key) VALUES (?,?,?,?,?)",
            (uid, today(), kind, amount, key),
        )
        return cur.rowcount == 1


def get_total_xp(uid: int) -> int:
    with conn() as c:
        row = c.execute("SELECT COALESCE(SUM(amount), 0) AS s FROM xp_events WHERE user_id=?", (uid,)).fetchone()
        return int(row["s"])


def get_active_days(uid: int) -> list[str]:
    """XP авсан өдрүүд, шинээс хуучин руу."""
    with conn() as c:
        rows = c.execute(
            "SELECT DISTINCT day FROM xp_events WHERE user_id=? ORDER BY day DESC", (uid,)
        ).fetchall()
        return [r["day"] for r in rows]
