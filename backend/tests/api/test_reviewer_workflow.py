from datetime import timedelta

import pytest

from app.core.security import now_utc


def _create_and_submit(client, applicant_headers, idx=0):
    payload = {
        "title": f"Reg-{idx}",
        "deadline_at": (now_utc() + timedelta(hours=24)).isoformat(),
        "form_data": {
            "applicant_name": "Alice",
            "id_number": "1234567890",
            "contact_phone": "13800138000",
            "activity_name": "Activity",
        },
    }
    reg = client.post("/registrations", json=payload, headers=applicant_headers).json()
    client.post(f"/registrations/{reg['id']}/submit", headers=applicant_headers)
    return reg["id"]


@pytest.mark.req2_state_machine
def test_state_machine_submitted_to_supplemented_to_approved(client, applicant_headers, reviewer_headers):
    reg_id = _create_and_submit(client, applicant_headers)

    res1 = client.post(
        f"/reviews/{reg_id}/action",
        json={"action": "supplement", "comments": "Need correction"},
        headers=reviewer_headers,
    )
    assert res1.status_code == 200
    assert res1.json()["status"] == "supplemented"

    res2 = client.post(
        f"/reviews/{reg_id}/action",
        json={"action": "approve", "comments": "Looks good"},
        headers=reviewer_headers,
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "approved"


@pytest.mark.req2_batch_50
def test_batch_review_exactly_50_entries(client, applicant_headers, reviewer_headers):
    ids = [_create_and_submit(client, applicant_headers, idx=i) for i in range(50)]
    batch = client.post(
        "/reviews/batch",
        json={"registration_ids": ids, "action": "approve", "comments": "batch"},
        headers=reviewer_headers,
    )
    assert batch.status_code == 200
    assert batch.json()["count"] == 50
