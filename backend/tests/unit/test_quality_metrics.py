import pytest

from app.core.security import now_utc
from app.models.entities import FundingAccount, FundingTransaction, QualityValidationResult, RegistrationForm
from app.models.enums import RegistrationStatus, TransactionType
from app.services.quality import generate_quality_metrics


@pytest.mark.req5_metrics
def test_quality_metrics_calculation_logic(db_session):
    ts = now_utc()
    regs = [
        RegistrationForm(
            applicant_id=1,
            title="A",
            form_data={},
            status=RegistrationStatus.approved,
            deadline_at=ts,
            created_at=ts,
            updated_at=ts,
        ),
        RegistrationForm(
            applicant_id=1,
            title="B",
            form_data={},
            status=RegistrationStatus.supplemented,
            deadline_at=ts,
            created_at=ts,
            updated_at=ts,
        ),
        RegistrationForm(
            applicant_id=1,
            title="C",
            form_data={},
            status=RegistrationStatus.rejected,
            deadline_at=ts,
            created_at=ts,
            updated_at=ts,
        ),
    ]
    db_session.add_all(regs)
    db_session.flush()

    acc1 = FundingAccount(registration_id=regs[0].id, budget_amount=1000, created_at=ts)
    acc2 = FundingAccount(registration_id=regs[1].id, budget_amount=1000, created_at=ts)
    db_session.add_all([acc1, acc2])
    db_session.flush()

    db_session.add_all(
        [
            FundingTransaction(
                account_id=acc1.id,
                transaction_type=TransactionType.expense,
                category="ops",
                amount=1200,
                note=None,
                invoice_path=None,
                created_at=ts,
            ),
            FundingTransaction(
                account_id=acc2.id,
                transaction_type=TransactionType.expense,
                category="ops",
                amount=900,
                note=None,
                invoice_path=None,
                created_at=ts,
            ),
        ]
    )
    db_session.commit()

    result = generate_quality_metrics(db_session)
    assert len(result) == 3

    rows = db_session.query(QualityValidationResult).all()
    table = {r.metric_key: r.metric_value for r in rows}
    assert table["approval_rate"] == pytest.approx(1 / 3)
    assert table["correction_rate"] == pytest.approx(1 / 3)
    assert table["overspending_rate"] == pytest.approx(1 / 2)
