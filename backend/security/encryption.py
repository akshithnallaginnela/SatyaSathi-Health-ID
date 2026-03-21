"""
Encryption utilities — password hashing, Aadhaar hashing, AES for wallet keys.
"""

import bcrypt
import hashlib
import base64
import os


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with salt rounds=12."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def hash_aadhaar(aadhaar_number: str) -> str:
    """
    Hash Aadhaar number using SHA-256 for uniqueness checks.
    We never store the raw Aadhaar — only this hash and last 4 digits.
    """
    salted = f"vitalid_aadhaar_salt_{aadhaar_number}"
    return hashlib.sha256(salted.encode("utf-8")).hexdigest()


def get_aadhaar_last4(aadhaar_number: str) -> str:
    """Get last 4 digits of Aadhaar for display purposes."""
    return aadhaar_number[-4:]


def mask_phone(phone: str) -> str:
    """Mask phone number for display: XXXXXXXX90."""
    if len(phone) >= 10:
        return "X" * (len(phone) - 2) + phone[-2:]
    return phone


def mask_aadhaar(aadhaar: str) -> str:
    """Mask Aadhaar for display: XXXX XXXX 1234."""
    if len(aadhaar) == 12:
        return f"XXXX XXXX {aadhaar[-4:]}"
    return aadhaar
