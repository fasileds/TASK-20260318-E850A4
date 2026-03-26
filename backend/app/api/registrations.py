from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep, require_roles
from app.core.config import settings
from app.core.security import ensure_utc, now_utc
from app.models.entities import RegistrationForm, User
from app.models.enums import RegistrationStatus, Role
from app.schemas.materials import SupplementRequest
from app.schemas.registration import RegistrationCreate, RegistrationOut, RegistrationUpdate
from app.services.validators import validate_registration_payload

router = APIRouter(prefix="/registrations", tags=["registrations"])


@router.post("", response_model=RegistrationOut)
def create_registration(
    payload: RegistrationCreate,
    db: Session = db_dep(),
    user: User = Depends(require_roles(Role.applicant)),
):
    validate_registration_payload(payload.form_data)
    now = now_utc()
    registration = RegistrationForm(
        applicant_id=user.id,
        title=payload.title,
        form_data=payload.form_data,
        deadline_at=payload.deadline_at,
        created_at=now,
        updated_at=now,
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return registration


@router.get("", response_model=list[RegistrationOut])
def list_registrations(
    db: Session = db_dep(),
    user: User = Depends(require_roles(Role.applicant, Role.reviewer, Role.financial_admin, Role.system_admin)),
):
    query = db.query(RegistrationForm)
    if user.role == Role.applicant:
        query = query.filter(RegistrationForm.applicant_id == user.id)
    return query.order_by(RegistrationForm.id.desc()).all()


@router.get("/{registration_id}/detail")
def registration_detail(
    registration_id: int,
    db: Session = db_dep(),
    user: User = Depends(require_roles(Role.applicant, Role.reviewer, Role.financial_admin, Role.system_admin)),
):
    registration = db.query(RegistrationForm).filter(RegistrationForm.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found")

    # Ownership / Permission Check (IDOR FIX)
    is_owner = user.id == registration.applicant_id
    is_privileged = user.role in {Role.system_admin, Role.reviewer, Role.financial_admin}
    
    if not is_owner and not is_privileged:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    data = dict(registration.form_data or {})
    # Masking for non-admins (even if it's the owner's own data? No, owner should probably see it).
    # Prompt says: "displayed with role-based masking". Usually means analysts see it masked.
    if user.role != Role.system_admin and not is_owner:
        if "id_number" in data and isinstance(data["id_number"], str):
            data["id_number"] = "********"
        if "contact_phone" in data and isinstance(data["contact_phone"], str):
            data["contact_phone"] = "********"

    return {
        "id": registration.id,
        "title": registration.title,
        "status": registration.status,
        "form_data": data,
        "deadline_at": registration.deadline_at,
    }


@router.patch("/{registration_id}", response_model=RegistrationOut)
def update_registration(
    registration_id: int,
    payload: RegistrationUpdate,
    db: Session = db_dep(),
    user: User = Depends(require_roles(Role.applicant)),
):
    registration = db.query(RegistrationForm).filter(RegistrationForm.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found")
    if registration.applicant_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    if ensure_utc(now_utc()) > ensure_utc(registration.deadline_at) and registration.status != RegistrationStatus.supplemented:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Materials and form locked after deadline")

    if payload.title is not None:
        registration.title = payload.title
    if payload.form_data is not None:
        validate_registration_payload(payload.form_data)
        registration.form_data = payload.form_data
    registration.updated_at = now_utc()
    db.commit()
    db.refresh(registration)
    return registration


@router.post("/{registration_id}/submit", response_model=RegistrationOut)
def submit_registration(
    registration_id: int,
    db: Session = db_dep(),
    user: User = Depends(require_roles(Role.applicant)),
):
    registration = db.query(RegistrationForm).filter(RegistrationForm.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found")
    if registration.applicant_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    registration.status = RegistrationStatus.submitted
    registration.updated_at = now_utc()
    db.commit()
    db.refresh(registration)
    return registration


@router.post("/{registration_id}/supplement", response_model=RegistrationOut)
def supplement_registration(
    registration_id: int,
    payload: SupplementRequest,
    db: Session = db_dep(),
    user: User = Depends(require_roles(Role.applicant)),
):
    registration = db.query(RegistrationForm).filter(RegistrationForm.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found")
    if registration.applicant_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    if registration.supplemented_once:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Supplement already used")

    supplement_deadline = registration.deadline_at + timedelta(hours=settings.supplement_window_hours)
    if ensure_utc(now_utc()) > ensure_utc(supplement_deadline):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Supplement window expired")

    registration.status = RegistrationStatus.supplemented
    registration.supplemented_once = True
    registration.form_data["supplement_reason"] = payload.reason
    registration.updated_at = now_utc()
    db.commit()
    db.refresh(registration)
    return registration
