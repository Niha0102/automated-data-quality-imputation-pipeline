from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker, create_async_engine
from app.core.config import settings

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker] = None


def _get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        kwargs: dict = {
            "echo": settings.ENVIRONMENT == "development",
            "pool_pre_ping": True,
        }
        # SQLite (used in tests) doesn't support pool_size / max_overflow
        if not settings.DATABASE_URL.startswith("sqlite"):
            kwargs["pool_size"] = 10
            kwargs["max_overflow"] = 20
        _engine = create_async_engine(settings.DATABASE_URL, **kwargs)
    return _engine


def _get_session_factory() -> async_sessionmaker:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with _get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
