import os
import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


TEST_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = TEST_ROOT.parent
TMP_ROOT = TEST_ROOT / ".tmp"
DB_PATH = TMP_ROOT / "test.db"
STORAGE_PATH = TMP_ROOT / "storage"
BACKUPS_PATH = TMP_ROOT / "backups"

TMP_ROOT.mkdir(parents=True, exist_ok=True)

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH.as_posix()}"
os.environ["LOCAL_STORAGE_ROOT"] = STORAGE_PATH.as_posix()
os.environ["BACKUP_ROOT"] = BACKUPS_PATH.as_posix()
os.environ["ENABLE_QUALITY_SCHEDULER"] = "false"

from app.bootstrap import seed_users  # noqa: E402
from app.core.crypto import encrypt_config_value
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db_and_storage():
    engine.dispose()
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except PermissionError:
            # On Windows, sometimes it takes a moment or ignore if it really fails
            pass
    if STORAGE_PATH.exists():
        shutil.rmtree(STORAGE_PATH)
    if BACKUPS_PATH.exists():
        shutil.rmtree(BACKUPS_PATH)
    STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    BACKUPS_PATH.mkdir(parents=True, exist_ok=True)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_users(db)
    finally:
        db.close()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_headers(username):
    token = encrypt_config_value(username)
    return {
        "Authorization": f"Bearer {token}",
        "X-Username": username  # Keep for legacy/support
    }


@pytest.fixture
def applicant_headers():
    return _get_headers("applicant_demo")


@pytest.fixture
def reviewer_headers():
    return _get_headers("reviewer_demo")


@pytest.fixture
def finance_headers():
    return _get_headers("finance_demo")


@pytest.fixture
def admin_headers():
    return _get_headers("admin_demo")
