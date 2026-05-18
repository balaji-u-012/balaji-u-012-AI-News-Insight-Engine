import asyncio

from backend.core.database import engine, Base
from backend.models import User, UserPreferences, NewsArticle, DigestLog, ScraperRun


async def reset_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Tables reset successfully")


if __name__ == "__main__":
    asyncio.run(reset_tables())