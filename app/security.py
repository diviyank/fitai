"""PURE auth helpers: no DB, no web. Password hashing + opaque session tokens."""
import secrets
import bcrypt


def hash_password(password: str) -> str:
    # bcrypt has a 72-byte limit on password input. Truncate UTF-8-encoded password
    # to 72 bytes to avoid ValueError and ensure consistent hashing.
    password_bytes = password.encode()[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    # bcrypt has a 72-byte limit on password input. Truncate UTF-8-encoded password
    # to 72 bytes to match hash_password's truncation for consistent verification.
    try:
        password_bytes = password.encode()[:72]
        return bcrypt.checkpw(password_bytes, password_hash.encode())
    except (ValueError, TypeError, AttributeError):
        return False


def new_token() -> str:
    return secrets.token_urlsafe(32)
