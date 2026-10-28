"""XP ба level систем (санааг Erdenetogs-ийн Spring Boot хувилбараас авав).

- Өнөөдрийн дасгалыг бүгдийг дуусгах: +40 XP (өдөрт 1 удаа)
- Жор хадгалах (хоол бүртгэх): +15 XP (жор бүрт өдөрт 1 удаа)
- Өдрийн анхны чат: +5 XP
- Level N → N+1: N × 100 XP
- Шат: Үр (1–2), Нахиа (3–4), Тамирчин (5–7), Аварга (8+)
"""
from datetime import date, timedelta

from app import db, i18n

XP = {"workout": 40, "meal": 15, "chat": 5}


def need(level: int) -> int:
    return 100 * level


def stage(level: int, lang: str = "mn") -> str:
    n = 4 if level >= 8 else 3 if level >= 5 else 2 if level >= 3 else 1
    return i18n.t(f"stage.{n}", lang)


def from_total(total: int, lang: str = "mn") -> dict:
    level, xp = 1, total
    while xp >= need(level):
        xp -= need(level)
        level += 1
    return {"level": level, "xp": xp, "need": need(level), "total": total,
            "stage": stage(level, lang), "pct": round(100 * xp / need(level))}


def streak(uid: int) -> int:
    """Өнөөдөр эсвэл өчигдрөөс эхлэн дараалан идэвхтэй байсан өдрийн тоо."""
    days = {date.fromisoformat(d) for d in db.get_active_days(uid)}
    cur = date.today()
    if cur not in days:
        cur -= timedelta(days=1)
    n = 0
    while cur in days:
        n += 1
        cur -= timedelta(days=1)
    return n


def status(uid: int, lang: str = "mn") -> dict:
    return {**from_total(db.get_total_xp(uid), lang), "streak": streak(uid)}


def award(uid: int, kind: str, key: str, lang: str = "mn") -> dict | None:
    """XP өгөөд frontend-д харуулах мэдээлэл буцаана. Аль хэдийн авсан бол None."""
    before = from_total(db.get_total_xp(uid))["level"]
    if not db.award_xp(uid, kind, XP[kind], key):
        return None
    st = status(uid, lang)
    return {"gained": XP[kind], "reason": i18n.t(f"xp.{kind}", lang), "leveled_up": st["level"] > before, **st}
