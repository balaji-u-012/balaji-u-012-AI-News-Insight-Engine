from datetime import datetime, timedelta
from operator import index
from typing import Optional

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.services.auth_service import get_current_user
from backend.services.scraper_service import run_all_scrapers
from backend.services.ranking_service import rank_articles

from backend.models.user import User
from backend.models.user_preferences import UserPreferences
from backend.models.article import NewsArticle


router = APIRouter()


@router.get("/feed")
async def get_news_feed(
    source: Optional[str] = Query(None),
    topic: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)

    filters = [
        NewsArticle.scraped_at >= since
    ]

    if source:
        filters.append(NewsArticle.source == source)

    if topic:
        filters.append(NewsArticle.topics.any(topic))

    result = await db.execute(
        select(NewsArticle)
        .where(and_(*filters))
        .order_by(desc(NewsArticle.final_rank_score))
        .limit(limit)
        .offset(offset)
    )

    articles = result.scalars().all()

    return {
        "articles": [
            {
                "id": str(a.id),
                "title": a.title,
                "url": a.url,
                "summary": a.summary,
                "source": a.source,
                "source_name": a.source_name,
                "published_at": (
                    a.published_at.isoformat()
                    if a.published_at
                    else None
                ),
                "topics": a.topics,
                "relevance_score": round(a.relevance_score or 0, 3),
                "engagement_score": round(a.engagement_score or 0, 3),
                "final_rank_score": round(a.final_rank_score or 0, 3),
                "thumbnail_url": a.thumbnail_url,
                "view_count": a.view_count,
            }
            for a in articles
        ],
        "total": len(articles),
        "offset": offset,
    }


@router.get("/top10")
async def get_top10(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prefs_result = await db.execute(
        select(UserPreferences).where(
            UserPreferences.user_id == current_user.id
        )
    )

    prefs = prefs_result.scalar_one_or_none()

    sources = prefs.sources if prefs else None
    topics = prefs.topics if prefs else []
    top_n = prefs.top_n if prefs else 10

    since = datetime.utcnow() - timedelta(days=3)

    filters = [
        NewsArticle.scraped_at >= since
    ]

    if sources:
        filters.append(NewsArticle.source.in_(sources))

    result = await db.execute(
        select(NewsArticle)
        .where(and_(*filters))
        .order_by(desc(NewsArticle.final_rank_score))
        .limit(top_n * 3)
    )

    articles = result.scalars().all()

    ranked = rank_articles(
        articles,
        user_topics=topics,
        user_sources=sources,
    )[:top_n]

    return {
        "articles": [
            {
                "rank": index + 1,
                "personalized_score": a.personalized_score,
                "id": str(a.id),
                "title": a.title,
                "url": a.url,
                "summary": a.summary,
                "source": a.source,
                "source_name": a.source_name,
                "published_at": (
                    a.published_at.isoformat()
                    if a.published_at
                    else None
                ),
                "topics": a.topics,
                "final_rank_score": round(a.final_rank_score or 0, 3),
                "thumbnail_url": a.thumbnail_url,
            }
            for a in ranked
        ]
    }


@router.post("/scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    background_tasks.add_task(run_all_scrapers)

    return {
        "message": "Scraping started in background"
    }