from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import (
    verify_password, hash_password, create_access_token, create_refresh_token, decode_token
)
from app.core.dependencies import get_current_user
from app.db.postgres import get_db
from app.db.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, RefreshRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Generic error — requirement 1.2: do NOT reveal which field is wrong
_INVALID_CREDS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    result = await db.execute(select(User).where(User.email == body.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        role="user",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # Always run verify_password to prevent timing attacks
    dummy_hash = "$2b$12$aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    stored_hash = user.password_hash if user else dummy_hash
    valid = verify_password(body.password, stored_hash)

    if not user or not valid or not user.is_active:
        raise _INVALID_CREDS

    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise JWTError("Not a refresh token")
        user_id: str = payload["sub"]
    except (JWTError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: User = Depends(get_current_user)):
    # Stateless JWT — client discards tokens. Refresh token blacklisting can be
    # added via Redis in a future iteration.
    return None


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
