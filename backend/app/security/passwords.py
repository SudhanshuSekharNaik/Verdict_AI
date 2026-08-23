import hashlib
import os
import secrets


def get_password_hash(password: str) -> str:
    """Secure PBKDF2-HMAC-SHA256 password hash with unique salt."""
    salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    ).hex()
    return f"{salt}${pw_hash}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against stored salt$hash."""
    try:
        salt, stored_hash = hashed_password.split("$")
        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000
        ).hex()
        return secrets.compare_digest(stored_hash, calculated_hash)
    except Exception:
        return False
