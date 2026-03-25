from collections import defaultdict
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.api.deps import db_dep, require_roles
from app.core.config import settings
from app.core.security import now_utc
from app.models.entities import FundingAccount, FundingTransaction, User
from app.models.enums import Role, TransactionType
from app.schemas.funding import FundingAccountCreate, FundingTransactionCreate, FundingTransactionOut

router = APIRouter(prefix="/funding", tags=["funding"])
ALLOWED_INVOICE_TYPES = {"application/pdf", "image/jpeg", "image/png"}


@router.post("/accounts")
def create_account(
    payload: FundingAccountCreate,
    db: Session = db_dep(),
    _: User = Depends(require_roles(Role.financial_admin)),
):
    account = FundingAccount(
        registration_id=payload.registration_id,
        budget_amount=payload.budget_amount,
        created_at=now_utc(),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return {"id": account.id, "budget_amount": float(account.budget_amount)}


@router.post("/transactions", response_model=FundingTransactionOut)
def create_transaction(
    payload: FundingTransactionCreate,
    db: Session = db_dep(),
    _: User = Depends(require_roles(Role.financial_admin)),
):
    account = db.query(FundingAccount).filter(FundingAccount.id == payload.account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funding account not found")

    tx_type = TransactionType(payload.transaction_type)
    
    # Calculate pre-transaction totals for warning
    expense_total = (
        db.query(func.coalesce(func.sum(FundingTransaction.amount), 0.0))
        .filter(FundingTransaction.account_id == payload.account_id)
        .filter(FundingTransaction.transaction_type == TransactionType.expense)
        .scalar()
    )
    
    new_expense_total = float(expense_total)
    if tx_type == TransactionType.expense:
        new_expense_total += float(payload.amount)

    warning = False
    if new_expense_total > float(account.budget_amount) * settings.overspending_ratio_threshold:
        warning = True

    if warning and not payload.confirmed_overspending:
        # Return the warning without committing
        return {
            "id": 0,
            "account_id": payload.account_id,
            "transaction_type": tx_type.value,
            "category": payload.category,
            "amount": float(payload.amount),
            "note": payload.note,
            "invoice_path": payload.invoice_path,
            "overspending_warning": True,
            "created_at": now_utc(),
        }

    transaction = FundingTransaction(
        account_id=payload.account_id,
        transaction_type=tx_type,
        category=payload.category,
        amount=payload.amount,
        note=payload.note,
        invoice_path=payload.invoice_path,
        created_at=now_utc(),
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return {
        "id": transaction.id,
        "account_id": transaction.account_id,
        "transaction_type": transaction.transaction_type.value,
        "category": transaction.category,
        "amount": float(transaction.amount),
        "note": transaction.note,
        "invoice_path": transaction.invoice_path,
        "overspending_warning": warning,
        "created_at": transaction.created_at,
    }


@router.post("/invoices/upload")
async def upload_invoice_attachment(
    account_id: int = Form(...),
    invoice: UploadFile = File(...),
    db: Session = db_dep(),
    _: User = Depends(require_roles(Role.financial_admin)),
):
    account = db.query(FundingAccount).filter(FundingAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funding account not found")

    if invoice.content_type not in ALLOWED_INVOICE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invoice type. Allowed: PDF/JPG/PNG")

    content = await invoice.read()
    if len(content) > settings.max_single_file_mb * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice exceeds 20MB")

    invoice_dir = Path(settings.local_storage_root) / "invoices" / f"account_{account_id}"
    invoice_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(invoice.filename or "").suffix.lower() or ".bin"
    file_name = f"invoice_{uuid4().hex}{suffix}"
    disk_path = invoice_dir / file_name
    disk_path.write_bytes(content)

    return {
        "account_id": account_id,
        "invoice_path": str(disk_path),
        "filename": file_name,
        "size_bytes": len(content),
    }


@router.get("/statistics")
def funding_statistics(
    account_id: int,
    year: int | None = None,
    month: int | None = None,
    db: Session = db_dep(),
    _: User = Depends(require_roles(Role.financial_admin, Role.system_admin)),
):
    query = db.query(FundingTransaction).filter(FundingTransaction.account_id == account_id)
    if year is not None:
        query = query.filter(extract("year", FundingTransaction.created_at) == year)
    if month is not None:
        query = query.filter(extract("month", FundingTransaction.created_at) == month)

    rows = query.all()
    by_category = defaultdict(float)
    by_type = defaultdict(float)
    for row in rows:
        by_category[row.category] += float(row.amount)
        by_type[row.transaction_type.value] += float(row.amount)

    return {
        "account_id": account_id,
        "filters": {"year": year, "month": month},
        "by_category": by_category,
        "by_type": by_type,
        "count": len(rows),
    }
