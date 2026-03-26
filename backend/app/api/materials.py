from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep, require_roles
from app.core.config import settings
from app.core.security import ensure_utc, now_utc
from app.models.entities import MaterialChecklistItem, MaterialVersion, RegistrationForm, User
from app.models.enums import MaterialStatus, Role
from app.schemas.materials import MaterialChecklistCreate
from app.services.validators import sha256_bytes, validate_file_type

router = APIRouter(prefix="/materials", tags=["materials"])
ALLOWED_LABELS = {"Pending Submission", "Submitted", "Needs Correction"}


@router.get("/similarity-check")
def similarity_check_reserved(enabled: bool = False):
    if not enabled:
        return {"enabled": False, "message": "Similarity/duplicate check interface reserved and disabled by default"}
    return {"enabled": True, "message": "Local-only implementation placeholder"}


@router.post("/{registration_id}/checklist")
def add_checklist_item(
    registration_id: int,
    payload: MaterialChecklistCreate,
    db: Session = db_dep(),
    user: User = Depends(require_roles(Role.system_admin, Role.applicant)),
):
    # Ownership Check (IDOR FIX)
    if user.role == Role.applicant:
        registration = db.query(RegistrationForm).filter(RegistrationForm.id == registration_id).first()
        if not registration:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found")
        if registration.applicant_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    item = MaterialChecklistItem(
        registration_id=registration_id,
        item_key=payload.item_key,
        display_name=payload.display_name,
        required=payload.required,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "status": item.status}


@router.post("/{checklist_item_id}/upload")
async def upload_material_version(
    checklist_item_id: int,
    file: UploadFile = File(...),
    label: str = Form("Submitted"),
    correction_reason: str | None = Form(default=None),
    db: Session = db_dep(),
    current_user: User = Depends(require_roles(Role.applicant)),
):
    checklist = db.query(MaterialChecklistItem).filter(MaterialChecklistItem.id == checklist_item_id).first()
    if not checklist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist item not found")
    if label not in ALLOWED_LABELS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid material label")

    registration = db.query(RegistrationForm).filter(RegistrationForm.id == checklist.registration_id).first()
    if not registration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found")
    
    # Ownership Check (IDOR FIX)
    if registration.applicant_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this registration")

    if ensure_utc(now_utc()) > ensure_utc(registration.deadline_at):
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Material locked after deadline")

    validate_file_type(file)
    content = await file.read()
    size_bytes = len(content)
    if size_bytes > settings.max_single_file_mb * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Single file exceeds 20MB")

    existing_versions = (
        db.query(MaterialVersion)
        .filter(MaterialVersion.checklist_item_id == checklist_item_id)
        .order_by(MaterialVersion.version_index.desc())
        .all()
    )

    total_bytes = size_bytes + sum(v.file_size_bytes for v in existing_versions)
    if total_bytes > settings.max_total_file_mb * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Total files exceed 200MB")

    if len(existing_versions) >= settings.max_material_versions:
        oldest = existing_versions[-1]
        old_path = Path(oldest.disk_path)
        if old_path.exists():
            old_path.unlink()
        db.delete(oldest)
        db.flush()

    fingerprint = sha256_bytes(content)
    duplicate = db.query(MaterialVersion).filter(MaterialVersion.sha256 == fingerprint).first()
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate material fingerprint detected")

    reg_storage = Path(settings.local_storage_root) / f"registration_{registration.id}" / checklist.item_key
    reg_storage.mkdir(parents=True, exist_ok=True)
    safe_name = file.filename or f"material_{checklist_item_id}.bin"
    disk_path = reg_storage / safe_name
    disk_path.write_bytes(content)

    next_idx = (existing_versions[0].version_index + 1) if existing_versions else 1
    version = MaterialVersion(
        checklist_item_id=checklist_item_id,
        version_index=next_idx,
        label=label,
        filename=safe_name,
        file_type=file.content_type or "application/octet-stream",
        file_size_bytes=size_bytes,
        sha256=fingerprint,
        disk_path=str(disk_path),
        correction_reason=correction_reason,
        created_at=now_utc(),
    )
    checklist.status = MaterialStatus.submitted
    db.add(version)
    db.commit()
    return {"version_id": version.id, "sha256": version.sha256, "status": checklist.status}
