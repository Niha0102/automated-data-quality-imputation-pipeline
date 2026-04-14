"""Unit tests for auth endpoints — Requirements 1.1, 1.2, 1.4."""
import pytest
from datetime import timedelta
from jose import jwt

from app.core.config import settings
from app.core.security import create_access_token, decode_token, hash_password


# ── /api/v1/auth/login ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_valid_credentials_returns_jwt(client, test_user):
    """Requirement 1.1: valid credentials → signed JWT returned."""
    resp = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "correct_password",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # Verify the token is decodable and contains correct claims
    payload = decode_token(data["access_token"])
    assert payload["sub"] == test_user.id
    assert payload["role"] == "user"


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client, test_user):
    """Requirement 1.2: invalid password → 401, generic message."""
    resp = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "wrong_password",
    })
    assert resp.status_code == 401
    # Must NOT reveal which field is wrong
    detail = resp.json()["detail"].lower()
    assert "password" not in detail
    assert "email" not in detail


@pytest.mark.asyncio
async def test_login_wrong_email_returns_401(client, test_user):
    """Requirement 1.2: unknown email → same generic 401."""
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "correct_password",
    })
    assert resp.status_code == 401
    detail = resp.json()["detail"].lower()
    assert "password" not in detail
    assert "email" not in detail


@pytest.mark.asyncio
async def test_login_inactive_user_returns_401(client, db_session):
    """Inactive users cannot log in."""
    from app.db.models import User
    user = User(
        email="inactive@example.com",
        password_hash=hash_password("password"),
        role="user",
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post("/api/v1/auth/login", json={
        "email": "inactive@example.com",
        "password": "password",
    })
    assert resp.status_code == 401


# ── /api/v1/auth/me (requires valid token) ────────────────────────────────────

@pytest.mark.asyncio
async def test_me_with_valid_token(client, test_user):
    """Requirement 1.3: valid JWT grants access to own resources."""
    token = create_access_token(test_user.id, test_user.role)
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_me_with_expired_token_returns_401(client, test_user):
    """Requirement 1.4: expired token → 401."""
    from datetime import datetime, timezone
    # Manually craft an expired token
    payload = {
        "sub": test_user.id,
        "role": test_user.role,
        "type": "access",
        "exp": datetime(2000, 1, 1, tzinfo=timezone.utc),
        "iat": datetime(2000, 1, 1, tzinfo=timezone.utc),
    }
    expired_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_no_token_returns_403(client):
    """No token → 403 (HTTPBearer returns 403 when no credentials provided)."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)


# ── /api/v1/auth/refresh ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_returns_new_access_token(client, test_user):
    """Valid refresh token → new access token issued."""
    from app.core.security import create_refresh_token
    refresh = create_refresh_token(test_user.id)
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails(client, test_user):
    """Using an access token as a refresh token must be rejected."""
    access = create_access_token(test_user.id, test_user.role)
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": access})
    assert resp.status_code == 401
