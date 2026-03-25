from datetime import timedelta

import pytest

from app.core.security import now_utc
from app.models.entities import MaterialChecklistItem, MaterialVersion, RegistrationForm


def _create_registration(client, applicant_headers, deadline_delta_hours=24):
    payload = {
        "title": "Reg A",
        "deadline_at": (now_utc() + timedelta(hours=deadline_delta_hours)).isoformat(),
        "form_data": {
            "applicant_name": "Alice",
            "id_number": "1234567890",
            "contact_phone": "13800138000",
            "activity_name": "Activity A",
        },
    }
    res = client.post("/registrations", json=payload, headers=applicant_headers)
    assert res.status_code == 200
    return res.json()["id"]


def _add_item(db_session, registration_id):
    item = MaterialChecklistItem(
        registration_id=registration_id,
        item_key="id_doc",
        display_name="ID Document",
        required=True,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item.id


@pytest.mark.req1_validation
def test_material_validation_file_types_and_sizes(client, db_session, applicant_headers):
    reg_id = _create_registration(client, applicant_headers)
    item_id = _add_item(db_session, reg_id)

    bad_type = client.post(
        f"/materials/{item_id}/upload",
        headers=applicant_headers,
        files={"file": ("virus.exe", b"evil", "application/x-msdownload")},
        data={"label": "Submitted"},
    )
    assert bad_type.status_code == 400

    too_big = client.post(
        f"/materials/{item_id}/upload",
        headers=applicant_headers,
        files={"file": ("big.pdf", b"a" * (20 * 1024 * 1024 + 1), "application/pdf")},
        data={"label": "Submitted"},
    )
    assert too_big.status_code == 400

    ok_pdf = client.post(
        f"/materials/{item_id}/upload",
        headers=applicant_headers,
        files={"file": ("ok.pdf", b"pdf-ok", "application/pdf")},
        data={"label": "Submitted"},
    )
    assert ok_pdf.status_code == 200

    ok_jpg = client.post(
        f"/materials/{item_id}/upload",
        headers=applicant_headers,
        files={"file": ("ok.jpg", b"jpg-ok", "image/jpeg")},
        data={"label": "Submitted"},
    )
    assert ok_jpg.status_code == 200

    ok_png = client.post(
        f"/materials/{item_id}/upload",
        headers=applicant_headers,
        files={"file": ("ok.png", b"png-ok", "image/png")},
        data={"label": "Submitted"},
    )
    assert ok_png.status_code == 200


@pytest.mark.req1_versioning
def test_material_versioning_keeps_latest_three(client, db_session, applicant_headers):
    reg_id = _create_registration(client, applicant_headers)
    item_id = _add_item(db_session, reg_id)

    for i in range(1, 5):
        res = client.post(
            f"/materials/{item_id}/upload",
            headers=applicant_headers,
            files={"file": (f"v{i}.pdf", f"content-{i}".encode(), "application/pdf")},
            data={"label": "Submitted"},
        )
        assert res.status_code == 200

    versions = (
        db_session.query(MaterialVersion)
        .filter(MaterialVersion.checklist_item_id == item_id)
        .order_by(MaterialVersion.version_index.asc())
        .all()
    )
    assert len(versions) == 3
    assert [v.version_index for v in versions] == [2, 3, 4]


@pytest.mark.req1_window
def test_supplement_window_71_accept_73_reject(monkeypatch, client, applicant_headers):
    now = now_utc()
    reg_id = _create_registration(client, applicant_headers, deadline_delta_hours=0)

    def fake_71():
        return now + timedelta(hours=71)

    monkeypatch.setattr("app.api.registrations.now_utc", fake_71)
    accepted = client.post(
        f"/registrations/{reg_id}/supplement",
        json={"reason": "fix data"},
        headers=applicant_headers,
    )
    assert accepted.status_code == 200

    reg_id_2 = _create_registration(client, applicant_headers, deadline_delta_hours=0)

    def fake_73():
        return now + timedelta(hours=73)

    monkeypatch.setattr("app.api.registrations.now_utc", fake_73)
    rejected = client.post(
        f"/registrations/{reg_id_2}/supplement",
        json={"reason": "late fix"},
        headers=applicant_headers,
    )
    assert rejected.status_code == 400


@pytest.mark.req1_locks
def test_material_locked_immediately_after_deadline(monkeypatch, client, db_session, applicant_headers):
    reg_id = _create_registration(client, applicant_headers, deadline_delta_hours=1)
    item_id = _add_item(db_session, reg_id)

    reg = db_session.query(RegistrationForm).filter(RegistrationForm.id == reg_id).first()

    def after_deadline():
        return reg.deadline_at + timedelta(seconds=1)

    monkeypatch.setattr("app.api.materials.now_utc", after_deadline)

    locked = client.post(
        f"/materials/{item_id}/upload",
        headers=applicant_headers,
        files={"file": ("late.pdf", b"late", "application/pdf")},
        data={"label": "Submitted"},
    )
    assert locked.status_code == 423
