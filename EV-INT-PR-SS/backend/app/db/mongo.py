from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGO_URL)
    return _client


def get_mongo_db() -> AsyncIOMotorDatabase:
    return get_mongo_client().get_default_database()


async def close_mongo_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


# Collection accessors
def reports_collection():
    return get_mongo_db()["reports"]


def logs_collection():
    return get_mongo_db()["processing_logs"]
