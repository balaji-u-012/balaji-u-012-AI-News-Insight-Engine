from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from pydantic import BaseModel

from typing import Optional

from backend.core.database import get_db

from backend.services.auth_service import (
    get_current_user,
)

from backend.models import User
from backend.models.user_preferences import UserPreferences


router = APIRouter()


# =========================================================
# Request Schema
# =========================================================

class PreferencesUpdate(BaseModel):

    topics: Optional[list[str]] = None

    sources: Optional[list[str]] = None

    digest_frequency: Optional[str] = None

    digest_time: Optional[str] = None

    top_n: Optional[int] = None

    email_enabled: Optional[bool] = None


# =========================================================
# Constants
# =========================================================

AVAILABLE_SOURCES = [
    "anthropic",
    "openai",
    "youtube",
    "reddit",
    "techcrunch",
    "arxiv",
]

AVAILABLE_TOPICS = [
    "llm",
    "computer-vision",
    "robotics",
    "ai-safety",
    "open-source",
    "research",
    "industry",
    "policy",
]


# =========================================================
# Get Preferences
# =========================================================

@router.get("/preferences")
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(
        select(UserPreferences).where(
            UserPreferences.user_id == current_user.id
        )
    )

    prefs = result.scalar_one_or_none()

    # Create defaults if missing
    if not prefs:

        prefs = UserPreferences(
            user_id=current_user.id
        )

        db.add(prefs)

        await db.commit()

        await db.refresh(prefs)

    return {
        "topics": prefs.topics,
        "sources": prefs.sources,
        "digest_frequency": prefs.digest_frequency,
        "digest_time": prefs.digest_time,
        "top_n": prefs.top_n,
        "email_enabled": prefs.email_enabled,
        "available_sources": AVAILABLE_SOURCES,
        "available_topics": AVAILABLE_TOPICS,
    }


# =========================================================
# Update Preferences
# =========================================================

@router.put("/preferences")
async def update_preferences(
    data: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(
        select(UserPreferences).where(
            UserPreferences.user_id == current_user.id
        )
    )

    prefs = result.scalar_one_or_none()

    if not prefs:

        prefs = UserPreferences(
            user_id=current_user.id
        )

        db.add(prefs)

    # -----------------------------------------------------
    # Topics
    # -----------------------------------------------------

    if data.topics is not None:

        prefs.topics = data.topics

    # -----------------------------------------------------
    # Sources
    # -----------------------------------------------------

    if data.sources is not None:

        if not all(
            source in AVAILABLE_SOURCES
            for source in data.sources
        ):

            raise HTTPException(
                status_code=400,
                detail="Invalid source provided",
            )

        prefs.sources = data.sources

    # -----------------------------------------------------
    # Digest Frequency
    # -----------------------------------------------------

    if data.digest_frequency is not None:

        if data.digest_frequency not in [
            "daily",
            "weekly",
        ]:

            raise HTTPException(
                status_code=400,
                detail="Frequency must be daily or weekly",
            )

        prefs.digest_frequency = (
            data.digest_frequency
        )

    # -----------------------------------------------------
    # Digest Time
    # -----------------------------------------------------

    if data.digest_time is not None:

        prefs.digest_time = data.digest_time

    # -----------------------------------------------------
    # Top N
    # -----------------------------------------------------

    if data.top_n is not None:

        prefs.top_n = max(
            1,
            min(20, data.top_n),
        )

    # -----------------------------------------------------
    # Email Enabled
    # -----------------------------------------------------

    if data.email_enabled is not None:

        prefs.email_enabled = data.email_enabled

    await db.commit()

    return {
        "message": "Preferences updated successfully"
    }