from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# bcrypt cost factor 12 (requirement 1.8)
_BCRYPT_ROUNDS = 12


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    # bcrypt requires bytes; truncate to 72 bytes (bcrypt hard limit)
    secret = plain.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(secret, bcrypt.gensalt(rounds=_BCRYPT_ROUNDS))
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    secret = plain.encode("utf-8")[:72]
    try:
        return bcrypt.checkpw(secret, hashed.encode("utf-8"))
    except Exception:
        return False


# ── JWT helpers ───────────────────────────────────────────────────────────────

def _make_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    payload["iat"] = datetime.now(timezone.utc)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: str, role: str) -> str:
    return _make_token(
        {"sub": user_id, "role": role, "type": "access"},
        timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> str:
    return _make_token(
        {"sub": user_id, "type": "refresh"},
        timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises JWTError on failure."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
