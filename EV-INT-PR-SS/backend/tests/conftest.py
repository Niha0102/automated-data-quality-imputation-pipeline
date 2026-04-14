"""Shared pytest fixtures for backend tests."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import patch

from app.main import app
from app.db.models import Base
from app.db.postgres import get_db
from app.core.security import hash_password

# In-memory SQLite for tests (no Postgres needed)
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """HTTP test client with DB override."""
    async def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    # Use bcrypt rounds=4 in tests for speed
    with patch("app.core.security._BCRYPT_ROUNDS", 4):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a regular test user in the DB."""
    from app.db.models import User
    import bcrypt
    # Use low cost factor for test speed
    secret = "correct_password".encode("utf-8")[:72]
    pw_hash = bcrypt.hashpw(secret, bcrypt.gensalt(rounds=4)).decode("utf-8")
    user = User(
        email="test@example.com",
        password_hash=pw_hash,
        role="user",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session):
    """Create an admin test user in the DB."""
    from app.db.models import User
    import bcrypt
    secret = "admin_password".encode("utf-8")[:72]
    pw_hash = bcrypt.hashpw(secret, bcrypt.gensalt(rounds=4)).decode("utf-8")
    user = User(
        email="admin@example.com",
        password_hash=pw_hash,
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
