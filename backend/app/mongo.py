import os
from motor.motor_asyncio import AsyncIOMotorClient


def get_mongo_client() -> AsyncIOMotorClient:
    mongo_url = os.environ.get("MONGO_URL")
    if not mongo_url:
        raise RuntimeError("MONGO_URL is not set")
    return AsyncIOMotorClient(mongo_url)


def get_db_name() -> str:
    return os.environ.get("DB_NAME", "test_database")
