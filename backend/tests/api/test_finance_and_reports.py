from datetime import timedelta

import pytest

from app.core.security import now_utc


def _create_registration(client, applicant_headers):
    payload = {
        "title": "Reg-Fin",
        "deadline_at": (now_utc() + timedelta(hours=24)).isoformat(),
        "form_data": {
            "applicant_name": "Alice",
            "id_number": "1234567890",
            "contact_phone": "13800138000",
            "activity_name": "Activity",
        },
    }
    return client.post("/registrations", json=payload, headers=applicant_headers).json()["id"]


@pytest.mark.req3_overspending
def test_overspending_warning_triggered_at_110_point_1_percent(client, applicant_headers, finance_headers):
    reg_id = _create_registration(client, applicant_headers)
    account = client.post(
        "/funding/accounts",
        json={"registration_id": reg_id, "budget_amount": 1000},
        headers=finance_headers,
    )
    assert account.status_code == 200
    account_id = account.json()["id"]

    tx = client.post(
        "/funding/transactions",
        json={
            "account_id": account_id,
            "transaction_type": "expense",
            "category": "ops",
            "amount": 1101,
            "note": "over budget",
            "invoice_path": None,
        },
        headers=finance_headers,
    )
    assert tx.status_code == 200
    assert tx.json()["overspending_warning"] is True


@pytest.mark.req3_reports
def test_report_exports_structure(client, admin_headers, finance_headers, reviewer_headers):
    rec = client.get("/system/reports/reconciliation", headers=finance_headers)
    assert rec.status_code == 200
    assert set(rec.json().keys()) >= {"report_type", "status", "format"}

    aud = client.get("/system/reports/audit", headers=reviewer_headers)
    assert aud.status_code == 200
    assert set(aud.json().keys()) >= {"report_type", "status", "format"}

    comp = client.get("/system/reports/compliance", headers=admin_headers)
    assert comp.status_code == 200
    assert set(comp.json().keys()) >= {"report_type", "status", "format"}
