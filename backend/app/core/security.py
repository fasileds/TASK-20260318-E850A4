import jwt
from datetime import datetime, timedelta, timezone

import bcrypt
from app.core.config import settings


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def lock_until(minutes: int) -> datetime:
    return now_utc() + timedelta(minutes=minutes)


def create_access_token(username: str, role: str) -> str:
    exp = now_utc() + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(
        {"sub": username, "role": role, "exp": exp},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
