import base64
import os

from cryptography.fernet import Fernet


def _build_key() -> bytes:
    raw = os.getenv("APP_CONFIG_SECRET", "local-dev-offline-secret")
    padded = (raw * (32 // len(raw) + 1))[:32].encode("utf-8")
    return base64.urlsafe_b64encode(padded)


def encrypt_config_value(value: str) -> str:
    return Fernet(_build_key()).encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_config_value(value: str) -> str:
    return Fernet(_build_key()).decrypt(value.encode("utf-8")).decode("utf-8")
