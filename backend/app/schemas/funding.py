from datetime import datetime

from pydantic import BaseModel, Field


class FundingAccountCreate(BaseModel):
    registration_id: int
    budget_amount: float = Field(gt=0)


class FundingTransactionCreate(BaseModel):
    account_id: int
    transaction_type: str
    category: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0)
    note: str | None = Field(default=None, max_length=2000)
    invoice_path: str | None = None


class FundingTransactionOut(BaseModel):
    id: int
    account_id: int
    transaction_type: str
    category: str
    amount: float
    note: str | None
    invoice_path: str | None
    overspending_warning: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
