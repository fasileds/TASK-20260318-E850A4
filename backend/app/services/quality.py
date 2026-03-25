from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import ensure_utc, now_utc
from app.models.entities import FundingAccount, FundingTransaction, QualityValidationResult, RegistrationForm
from app.models.enums import RegistrationStatus, TransactionType


def generate_quality_metrics(db: Session) -> list[QualityValidationResult]:
    total = db.query(func.count(RegistrationForm.id)).scalar() or 1
    approved = (
        db.query(func.count(RegistrationForm.id))
        .filter(RegistrationForm.status == RegistrationStatus.approved)
        .scalar()
        or 0
    )
    supplemented = (
        db.query(func.count(RegistrationForm.id))
        .filter(RegistrationForm.status == RegistrationStatus.supplemented)
        .scalar()
        or 0
    )

    approval_rate = approved / total
    correction_rate = supplemented / total
    overspending_rate = _calculate_overspending_rate(db)

    records = [
        _store_metric(db, "approval_rate", approval_rate, 0.6),
        _store_metric(db, "correction_rate", correction_rate, 0.4),
        _store_metric(db, "overspending_rate", overspending_rate, 0.1),
    ]
    db.commit()
    return records


def _calculate_overspending_rate(db: Session) -> float:
    accounts = db.query(FundingAccount).all()
    if not accounts:
        return 0.0

    overspending_accounts = 0
    for account in accounts:
        expense_total = (
            db.query(func.coalesce(func.sum(FundingTransaction.amount), 0))
            .filter(FundingTransaction.account_id == account.id)
            .filter(FundingTransaction.transaction_type == TransactionType.expense)
            .scalar()
        )
        if float(expense_total) > float(account.budget_amount) * settings.overspending_ratio_threshold:
            overspending_accounts += 1

    return overspending_accounts / len(accounts)


def _store_metric(db: Session, key: str, value: float, threshold: float) -> QualityValidationResult:
    generated_at = ensure_utc(now_utc())
    metric = QualityValidationResult(
        metric_key=key,
        metric_value=value,
        threshold=threshold,
        exceeded=value > threshold,
        generated_at=generated_at,
    )
    db.add(metric)
    return metric
