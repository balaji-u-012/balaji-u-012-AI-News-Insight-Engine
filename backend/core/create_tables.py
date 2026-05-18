import asyncio

from backend.core.database import engine, Base

from backend.models.user import User
from backend.models.user_preferences import UserPreferences
from backend.models.article import NewsArticle
from backend.models.digest_log import DigestLog


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Tables recreated successfully")


if __name__ == "__main__":
    asyncio.run(create_tables())