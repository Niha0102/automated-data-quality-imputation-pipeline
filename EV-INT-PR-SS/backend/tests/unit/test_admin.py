"""Unit tests for admin endpoints — Task 4.5."""
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token


def _auth_headers(user) -> dict:
    token = create_access_token(str(user.id), user.role)
    return {"Authorization": f"Bearer {token}"}


# ── 4.5a: Non-admin user is forbidden ────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_users_forbidden_for_regular_user(client: AsyncClient, test_user):
    """Regular user accessing /admin/users must receive HTTP 403."""
    response = await client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(test_user),
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


@pytest.mark.asyncio
async def test_create_user_forbidden_for_regular_user(client: AsyncClient, test_user):
    """Regular user POSTing to /admin/users must receive HTTP 403."""
    response = await client.post(
        "/api/v1/admin/users",
        json={"email": "new@example.com", "password": "pass1234", "role": "user"},
        headers=_auth_headers(test_user),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_user_forbidden_for_regular_user(client: AsyncClient, test_user):
    """Regular user PATCHing /admin/users/{id} must receive HTTP 403."""
    response = await client.patch(
        f"/api/v1/admin/users/{test_user.id}",
        json={"role": "admin"},
        headers=_auth_headers(test_user),
    )
    assert response.status_code == 403


# ── 4.5b: Admin user can manage users ────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_users_succeeds_for_admin(client: AsyncClient, admin_user, test_user):
    """Admin can list users and receives paginated response."""
    response = await client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(admin_user),
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2  # admin + test_user both exist


@pytest.mark.asyncio
async def test_create_user_succeeds_for_admin(client: AsyncClient, admin_user):
    """Admin can create a new user."""
    response = await client.post(
        "/api/v1/admin/users",
        json={"email": "newuser@example.com", "password": "securepass", "role": "user"},
        headers=_auth_headers(admin_user),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "user"


@pytest.mark.asyncio
async def test_create_user_duplicate_email_returns_409(client: AsyncClient, admin_user, test_user):
    """Creating a user with an existing email returns 409."""
    response = await client.post(
        "/api/v1/admin/users",
        json={"email": test_user.email, "password": "pass", "role": "user"},
        headers=_auth_headers(admin_user),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_user_role_succeeds_for_admin(client: AsyncClient, admin_user, test_user):
    """Admin can update a user's role."""
    response = await client.patch(
        f"/api/v1/admin/users/{test_user.id}",
        json={"role": "admin"},
        headers=_auth_headers(admin_user),
    )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_update_nonexistent_user_returns_404(client: AsyncClient, admin_user):
    """Updating a user that doesn't exist returns 404."""
    response = await client.patch(
        "/api/v1/admin/users/nonexistent-id",
        json={"is_active": False},
        headers=_auth_headers(admin_user),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_request_returns_403(client: AsyncClient):
    """Request without token to admin endpoint returns 403 (no bearer = forbidden)."""
    response = await client.get("/api/v1/admin/users")
    assert response.status_code in (401, 403)
