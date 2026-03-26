from datetime import timedelta


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.core.config import settings
from app.core.security import create_access_token, ensure_utc, now_utc, verify_password
from app.models.entities import User
from app.schemas.auth import LoginOut, LoginRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginOut)
def login(payload: LoginRequest, db: Session = db_dep()):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    now = now_utc()
    if user.locked_until and ensure_utc(user.locked_until) > ensure_utc(now):
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account temporarily locked")

    if verify_password(payload.password, user.password_hash):
        user.failed_attempts = 0
        user.first_failed_at = None
        user.locked_until = None
        db.commit()
        token = create_access_token(
            username=user.username,
            role=user.role.value if hasattr(user.role, "value") else str(user.role)
        )
        return {"user": user, "token": token}

    window = timedelta(minutes=settings.login_window_minutes)
    first_failed_at = ensure_utc(user.first_failed_at) if user.first_failed_at else None
    if not first_failed_at or ensure_utc(now) - first_failed_at > window:
        user.first_failed_at = now
        user.failed_attempts = 1
    else:
        user.failed_attempts += 1

    if user.failed_attempts >= settings.login_max_failed_attempts:
        user.locked_until = now + timedelta(minutes=settings.login_lock_minutes)

    db.commit()
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
