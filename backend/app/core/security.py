"""Password hashing (bcrypt) and JWT issue/verify helpers."""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings

_ALGORITHM = "HS256"


def _pw_bytes(password: str) -> bytes:
    # bcrypt rejects inputs over 72 bytes; truncate consistently on hash & verify.
    return password.encode()[:72]


def hash_password(password: str) -> str:
    """Return a bcrypt hash of ``password`` (salt embedded, cost 12 default)."""
    return bcrypt.hashpw(_pw_bytes(password), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Constant-time check of ``password`` against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(_pw_bytes(password), password_hash.encode())
    except ValueError:
        # Malformed hash in the DB — treat as no match rather than 500.
        return False


def create_access_token(subject: str) -> str:
    """Issue a signed HS256 token carrying ``sub`` and an ``exp`` claim."""
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=_ALGORITHM)


def decode_token(token: str) -> str | None:
    """Return the token's ``sub``, or ``None`` if invalid/expired/malformed."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[_ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    sub = payload.get("sub")
    return sub if isinstance(sub, str) else None
