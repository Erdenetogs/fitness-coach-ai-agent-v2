"""Нэвтрэх: имэйл шалгах, нууц үг hash хийх, олон удаа буруу оролдлогыг түр хаах.

Нууц үгийг хэзээ ч шууд хадгалахгүй. Python-д угаасаа байдаг scrypt-ээр hash хийж,
хэрэглэгч бүрт санамсаргүй давс (salt) нэмнэ. Өгөгдлийн сан алдагдсан ч нууц үг ил гарахгүй.
"""
import base64
import hashlib
import hmac
import re
import secrets
import time

# scrypt-ийн тохиргоо: нэг hash ~16MB санах ой, ~50мс — brute force-ийг удаашруулна
_N, _R, _P, _LEN = 2 ** 14, 8, 1, 32

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_MIN, PASSWORD_MAX = 8, 128


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()[:120]


def valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


def valid_password(password: str) -> bool:
    return PASSWORD_MIN <= len(password or "") <= PASSWORD_MAX


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=_LEN)
    return f"scrypt${_N}${_R}${_P}${_b64(salt)}${_b64(dk)}"


def verify_password(password: str, stored: str | None) -> bool:
    try:
        algo, n, r, p, salt, expected = (stored or "").split("$")
        if algo != "scrypt":
            return False
        dk = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt),
                            n=int(n), r=int(r), p=int(p), dklen=len(base64.b64decode(expected)))
        return hmac.compare_digest(dk, base64.b64decode(expected))
    except (ValueError, TypeError):
        return False


# Ийм имэйл байхгүй үед ч hash тооцож, хариу өгөх хугацаагаар имэйл бүртгэлтэй эсэхийг таахгүй болгоно
_DUMMY = hash_password(secrets.token_urlsafe(16))


def check_login(password: str, stored: str | None) -> bool:
    return verify_password(password, stored if stored else _DUMMY) and bool(stored)


# ---------- Олон удаа буруу оролдвол түр хаах ----------
MAX_FAILS, WINDOW_S = 5, 15 * 60
_fails: dict[str, list[float]] = {}


def locked(email: str) -> bool:
    now = time.time()
    recent = [t for t in _fails.get(email, []) if now - t < WINDOW_S]
    _fails[email] = recent
    return len(recent) >= MAX_FAILS


def record_fail(email: str):
    _fails.setdefault(email, []).append(time.time())


def clear_fails(email: str):
    _fails.pop(email, None)
