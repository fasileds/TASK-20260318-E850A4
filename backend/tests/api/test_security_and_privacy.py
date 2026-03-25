from datetime import timedelta

import pytest

from app.core.config import settings
from app.core.security import ensure_utc, now_utc
from app.models.entities import MaterialChecklistItem, User


def _create_registration(client, applicant_headers):
    payload = {
        "title": "Reg-Sec",
        "deadline_at": (now_utc() + timedelta(hours=24)).isoformat(),
        "form_data": {
            "applicant_name": "Alice",
            "id_number": "1234567890",
            "contact_phone": "13800138000",
            "activity_name": "Activity",
        },
    }
    return client.post("/registrations", json=payload, headers=applicant_headers).json()["id"]


@pytest.mark.req4_lockout
def test_login_lockout_after_tenth_failed_attempt_within_five_minutes(monkeypatch, client, db_session):
    base = now_utc()
    current = {"value": base}

    def fake_now():
        return current["value"]

    monkeypatch.setattr("app.api.auth.now_utc", fake_now)

    for i in range(10):
        current["value"] = base + timedelta(seconds=i * 20)
        fail = client.post("/auth/login", json={"username": "applicant_demo", "password": "wrongpass1"})
        assert fail.status_code == 401

    current["value"] = base + timedelta(minutes=4)
    locked = client.post("/auth/login", json={"username": "applicant_demo", "password": "Applicant@123"})
    assert locked.status_code == 423

    user = db_session.query(User).filter(User.username == "applicant_demo").first()
    assert user.locked_until is not None
    locked_until = user.locked_until
    expected_locked_until = base + timedelta(seconds=180, minutes=settings.login_lock_minutes)
    assert abs((ensure_utc(locked_until) - ensure_utc(expected_locked_until)).total_seconds()) < 1

    current["value"] = locked_until - timedelta(seconds=1)
    still_locked = client.post("/auth/login", json={"username": "applicant_demo", "password": "Applicant@123"})
    assert still_locked.status_code == 423

    current["value"] = locked_until + timedelta(seconds=1)
    unlocked = client.post("/auth/login", json={"username": "applicant_demo", "password": "Applicant@123"})
    assert unlocked.status_code == 200


@pytest.mark.req4_masking
def test_masking_non_admin_sees_stars(client, applicant_headers, reviewer_headers):
    reg_id = _create_registration(client, applicant_headers)
    detail = client.get(f"/registrations/{reg_id}/detail", headers=reviewer_headers)
    assert detail.status_code == 200
    form_data = detail.json()["form_data"]
    assert form_data["id_number"] == "********"
    assert form_data["contact_phone"] == "********"


@pytest.mark.req4_fingerprint
def test_sha256_duplicate_detector_blocks_same_content(client, db_session, applicant_headers):
    reg_id = _create_registration(client, applicant_headers)
    item = MaterialChecklistItem(
        registration_id=reg_id,
        item_key="doc",
        display_name="Document",
        required=True,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    first = client.post(
        f"/materials/{item.id}/upload",
        headers=applicant_headers,
        files={"file": ("a.pdf", b"same-content", "application/pdf")},
        data={"label": "Submitted"},
    )
    assert first.status_code == 200

    second = client.post(
        f"/materials/{item.id}/upload",
        headers=applicant_headers,
        files={"file": ("b.pdf", b"same-content", "application/pdf")},
        data={"label": "Submitted"},
    )
    assert second.status_code == 409


@pytest.mark.security_idor
def test_idor_prevention_user_cannot_access_other_registration(client, db_session, applicant_headers):
    # Create registration for user A
    reg_id_a = _create_registration(client, applicant_headers)

    # Create user B (another applicant)
    from app.core.security import hash_password
    from app.models.enums import Role
    user_b = User(
        username="applicant_b",
        password_hash=hash_password("ApplicantB@123"),
        role=Role.applicant,
    )
    db_session.add(user_b)
    db_session.commit()
    
    # Login as user B
    login_res = client.post("/auth/login", json={"username": "applicant_b", "password": "ApplicantB@123"})
    assert login_res.status_code == 200
    token = login_res.json()["token"]
    # Using Authorization header with token
    headers_b = {"Authorization": f"Bearer {token}"}

    # Try to access user A's registration (should be 403)
    res = client.get(f"/registrations/{reg_id_a}/detail", headers=headers_b)
    assert res.status_code == 403
    
    # Check update access (IDOR on write)
    res_update = client.patch(f"/registrations/{reg_id_a}", json={"title": "Hacked"}, headers=headers_b)
    assert res_update.status_code == 403
