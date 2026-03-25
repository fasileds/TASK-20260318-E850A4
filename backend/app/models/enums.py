from enum import Enum


class Role(str, Enum):
    applicant = "applicant"
    reviewer = "reviewer"
    financial_admin = "financial_admin"
    system_admin = "system_admin"


class MaterialStatus(str, Enum):
    pending_submission = "pending_submission"
    submitted = "submitted"
    needs_correction = "needs_correction"
    locked = "locked"


class RegistrationStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    supplemented = "supplemented"
    approved = "approved"
    rejected = "rejected"
    canceled = "canceled"
    promoted_from_waitlist = "promoted_from_waitlist"


class ReviewAction(str, Enum):
    submit = "submit"
    supplement = "supplement"
    approve = "approve"
    reject = "reject"
    cancel = "cancel"
    promote = "promote"


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"
