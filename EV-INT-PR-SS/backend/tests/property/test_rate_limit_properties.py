"""
Property test for rate limiting.

Feature: ai-data-quality-platform, Property 10: Rate limiting enforcement
Validates: Requirements 15.4
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.core.security import create_access_token
from app.core.middleware import RATE_LIMIT


@pytest.mark.asyncio
async def test_rate_limit_enforced_at_101st_request(client, test_user):
    """
    Property 10: Rate limiting enforcement
    For any authenticated user, submitting more than 100 requests within
    60 seconds SHALL result in HTTP 429 for all requests beyond the 100th.
    Validates: Requirements 15.4
    """
    token = create_access_token(test_user.id, test_user.role)
    headers = {"Authorization": f"Bearer {token}"}

    # Use a fake Redis that counts in-memory so the test is self-contained
    counter = {"count": 0}

    async def fake_incr(key):
        counter["count"] += 1
        return counter["count"]

    async def fake_expire(key, ttl):
        pass

    async def fake_ttl(key):
        return 45

    mock_redis = AsyncMock()
    mock_redis.incr = fake_incr
    mock_redis.expire = fake_expire
    mock_redis.ttl = fake_ttl

    with patch("app.core.middleware.get_redis", return_value=mock_redis):
        # First RATE_LIMIT requests should all succeed (or at least not 429)
        for i in range(RATE_LIMIT):
            resp = await client.get("/health", headers=headers)
            assert resp.status_code != 429, f"Request {i+1} was unexpectedly rate-limited"

        # The (RATE_LIMIT + 1)th request must return 429
        resp = await client.get("/health", headers=headers)
        assert resp.status_code == 429, "Expected HTTP 429 after exceeding rate limit"
        assert "Retry-After" in resp.headers
        body = resp.json()
        assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_rate_limit_includes_retry_after_header(client, test_user):
    """429 response must include Retry-After header — Requirement 15.4."""
    token = create_access_token(test_user.id, test_user.role)
    headers = {"Authorization": f"Bearer {token}"}

    counter = {"count": RATE_LIMIT + 1}  # already over limit

    async def fake_incr(key):
        return counter["count"]

    async def fake_expire(key, ttl):
        pass

    async def fake_ttl(key):
        return 30

    mock_redis = AsyncMock()
    mock_redis.incr = fake_incr
    mock_redis.expire = fake_expire
    mock_redis.ttl = fake_ttl

    with patch("app.core.middleware.get_redis", return_value=mock_redis):
        resp = await client.get("/health", headers=headers)
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers
        assert int(resp.headers["Retry-After"]) > 0


@pytest.mark.asyncio
async def test_unauthenticated_requests_not_rate_limited(client):
    """Unauthenticated requests bypass rate limiting."""
    # /health has no auth — should always return 200 regardless of counter
    for _ in range(5):
        resp = await client.get("/health")
        assert resp.status_code == 200
