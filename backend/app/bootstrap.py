from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.entities import User
from app.models.enums import Role


def seed_users(db: Session) -> None:
    defaults = [
        ("applicant_demo", "Applicant@123", Role.applicant),
        ("reviewer_demo", "Reviewer@123", Role.reviewer),
        ("finance_demo", "Finance@123", Role.financial_admin),
        ("admin_demo", "Admin@123", Role.system_admin),
    ]
    for username, password, role in defaults:
        exists = db.query(User).filter(User.username == username).first()
        if exists:
            continue
        db.add(User(username=username, password_hash=hash_password(password), role=role))
    db.commit()
