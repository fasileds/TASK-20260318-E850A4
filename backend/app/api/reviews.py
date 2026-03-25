from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep, require_roles
from app.core.security import now_utc
from app.models.entities import RegistrationForm, ReviewWorkflowRecord, User
from app.models.enums import RegistrationStatus, ReviewAction, Role
from app.schemas.review import BatchReviewRequest, ReviewActionRequest
from app.services.review_flow import next_status

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/{registration_id}/action")
def review_action(
    registration_id: int,
    payload: ReviewActionRequest,
    db: Session = db_dep(),
    reviewer: User = Depends(require_roles(Role.reviewer)),
):
    registration = db.query(RegistrationForm).filter(RegistrationForm.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found")

    try:
        action = ReviewAction(payload.action)
        next_state = next_status(registration.status, action)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    record = ReviewWorkflowRecord(
        registration_id=registration.id,
        reviewer_id=reviewer.id,
        action=action,
        from_status=registration.status,
        to_status=next_state,
        comments=payload.comments,
        created_at=now_utc(),
    )
    registration.status = next_state
    registration.updated_at = now_utc()
    db.add(record)
    db.commit()
    return {"registration_id": registration.id, "status": registration.status}


@router.post("/batch")
def batch_review(
    payload: BatchReviewRequest,
    db: Session = db_dep(),
    reviewer: User = Depends(require_roles(Role.reviewer)),
):
    if len(payload.registration_ids) > 50:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Batch limit is 50")

    updated: list[dict] = []
    for rid in payload.registration_ids:
        registration = db.query(RegistrationForm).filter(RegistrationForm.id == rid).first()
        if not registration:
            continue
        try:
            action = ReviewAction(payload.action)
            to_state = next_status(registration.status, action)
        except ValueError:
            continue

        db.add(
            ReviewWorkflowRecord(
                registration_id=registration.id,
                reviewer_id=reviewer.id,
                action=action,
                from_status=registration.status,
                to_status=to_state,
                comments=payload.comments,
                created_at=now_utc(),
            )
        )
        registration.status = to_state
        registration.updated_at = now_utc()
        updated.append({"registration_id": registration.id, "status": to_state})

    db.commit()
    return {"updated": updated, "count": len(updated)}


@router.get("/{registration_id}/logs")
def review_logs(
    registration_id: int,
    db: Session = db_dep(),
    _: User = Depends(require_roles(Role.reviewer, Role.system_admin)),
):
    records = (
        db.query(ReviewWorkflowRecord)
        .filter(ReviewWorkflowRecord.registration_id == registration_id)
        .order_by(ReviewWorkflowRecord.created_at.asc())
        .all()
    )
    return [
        {
            "action": r.action,
            "from": r.from_status,
            "to": r.to_status,
            "comments": r.comments,
            "created_at": r.created_at,
        }
        for r in records
    ]
