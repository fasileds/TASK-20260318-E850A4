from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png"}
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


def validate_file_type(file: UploadFile) -> None:
    extension = Path(file.filename or "").suffix.lower()
    if file.content_type not in ALLOWED_TYPES and extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed: PDF/JPG/PNG.",
        )


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def validate_registration_payload(form_data: dict) -> None:
    mandatory_fields = ["applicant_name", "id_number", "contact_phone", "activity_name"]
    missing = [f for f in mandatory_fields if not form_data.get(f)]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing mandatory fields: {', '.join(missing)}",
        )


def mask_sensitive(value: str, left: int = 2, right: int = 2) -> str:
    if len(value) <= left + right:
        return "*" * len(value)
    return value[:left] + "*" * (len(value) - left - right) + value[-right:]
