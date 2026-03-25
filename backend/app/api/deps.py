from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.crypto import decrypt_config_value
from app.core.database import get_db
from app.models.entities import User
from app.models.enums import Role


def db_dep():
    return Depends(get_db)


def get_current_user(
    auth_header: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    username = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            username = decrypt_config_value(token)
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")
        
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user session")
    return user


def require_roles(*roles: Role):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return user

    return checker
