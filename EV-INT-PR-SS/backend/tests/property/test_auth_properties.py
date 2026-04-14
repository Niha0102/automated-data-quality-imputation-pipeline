"""
Property tests for auth security module.

Feature: ai-data-quality-platform
Property 9: JWT authentication validity
"""
import pytest
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st

from app.core.security import (
    create_access_token, create_refresh_token, decode_token,
    hash_password, verify_password,
)

h_settings.register_profile("ci", max_examples=20)
h_settings.load_profile("ci")

# ── Strategies ────────────────────────────────────────────────────────────────

_uuid_strategy = st.uuids().map(str)
_role_strategy = st.sampled_from(["user", "admin"])
# bcrypt hard limit is 72 bytes; filter to ensure encoded length stays within bounds
_password_strategy = st.text(min_size=1, max_size=50).filter(
    lambda p: len(p.encode("utf-8")) <= 72
)


# ── Property 9: JWT authentication validity ───────────────────────────────────
# Feature: ai-data-quality-platform, Property 9: JWT authentication validity

@given(user_id=_uuid_strategy, role=_role_strategy)
@h_settings(max_examples=20, deadline=None)
def test_jwt_access_token_round_trip(user_id: str, role: str):
    """For any user_id and role, creating then decoding an access token returns
    the original claims without error."""
    token = create_access_token(user_id, role)
    payload = decode_token(token)

    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "access"


@given(user_id=_uuid_strategy)
@h_settings(max_examples=20, deadline=None)
def test_jwt_refresh_token_round_trip(user_id: str):
    """For any user_id, creating then decoding a refresh token returns the
    original user_id without error."""
    token = create_refresh_token(user_id)
    payload = decode_token(token)

    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"


# ── Property: bcrypt cost factor ──────────────────────────────────────────────
# Validates: Requirements 1.8

@given(password=_password_strategy)
@h_settings(max_examples=5, deadline=None)
def test_bcrypt_cost_factor_12(password: str):
    """For any password string, the hash starts with $2b$12$ indicating
    bcrypt with cost factor 12."""
    hashed = hash_password(password)
    assert hashed.startswith("$2b$12$"), f"Expected cost factor 12, got: {hashed[:10]}"


@given(password=_password_strategy)
@h_settings(max_examples=5, deadline=None)
def test_password_verify_round_trip(password: str):
    """For any password, hashing then verifying returns True."""
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


@given(password=_password_strategy, wrong=_password_strategy)
@h_settings(max_examples=5, deadline=None)
def test_wrong_password_rejected(password: str, wrong: str):
    """For any two distinct passwords, verifying the wrong one returns False."""
    if password == wrong:
        return  # skip equal case
    hashed = hash_password(password)
    assert verify_password(wrong, hashed) is False
