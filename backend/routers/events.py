from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.services.auth_service import (
    get_current_user,
)
from backend.services.preference_learning_service import (
    update_user_preferences_from_events,
)

from backend.models import User
from backend.models.article import NewsArticle
from backend.models.user_event import UserEvent


router = APIRouter()


class EventCreate(BaseModel):
    article_id: UUID
    event_type: str


VALID_EVENTS = [
    "click",
    "like",
    "save",
    "dismiss",
]


@router.post("/track")
async def track_user_event(
    data: EventCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: AsyncSession = Depends(get_db),
):
    if data.event_type not in VALID_EVENTS:
        raise HTTPException(
            status_code=400,
            detail="Invalid event type",
        )

    article_result = await db.execute(
        select(NewsArticle).where(
            NewsArticle.id == data.article_id
        )
    )

    article = article_result.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    event = UserEvent(
        user_id=current_user.id,
        article_id=data.article_id,
        event_type=data.event_type,
    )

    db.add(event)
    await db.commit()

    prefs = await update_user_preferences_from_events(
        user_id=current_user.id,
        db=db,
    )

    return {
        "message": "User preference updated automatically",
        "topics": prefs.topics,
        "sources": prefs.sources,
    }


@router.get("/email-click")
async def email_click(
    user_id: UUID = Query(...),
    article_id: UUID = Query(...),
    redirect_url: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    article_result = await db.execute(
        select(NewsArticle).where(
            NewsArticle.id == article_id
        )
    )

    article = article_result.scalar_one_or_none()

    if article:
        event = UserEvent(
            user_id=user_id,
            article_id=article_id,
            event_type="click",
        )

        db.add(event)
        await db.commit()

        await update_user_preferences_from_events(
            user_id=user_id,
            db=db,
        )

    return RedirectResponse(
        url=redirect_url,
        status_code=302,
    )


@router.get("/email-action")
async def email_action(
    user_id: UUID = Query(...),
    article_id: UUID = Query(...),
    event_type: str = Query(...),
    redirect_url: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        if event_type in VALID_EVENTS:
            article_result = await db.execute(
                select(NewsArticle).where(
                    NewsArticle.id == article_id
                )
            )

            article = article_result.scalar_one_or_none()

            if article:
                event = UserEvent(
                    user_id=user_id,
                    article_id=article_id,
                    event_type=event_type,
                )

                db.add(event)
                await db.commit()

                await update_user_preferences_from_events(
                    user_id=user_id,
                    db=db,
                )

    except Exception as e:
        print("Email action tracking failed:", e)

    return RedirectResponse(
        url=redirect_url,
        status_code=302,
    )

    article = article_result.scalar_one_or_none()

    if article:
        event = UserEvent(
            user_id=user_id,
            article_id=article_id,
            event_type=event_type,
        )

        db.add(event)
        await db.commit()

        await update_user_preferences_from_events(
            user_id=user_id,
            db=db,
        )

    return RedirectResponse(
        url=redirect_url,
        status_code=302,
    )