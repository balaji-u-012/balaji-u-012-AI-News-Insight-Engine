import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_, desc

from backend.core.database import AsyncSessionLocal
from backend.models.user import User
from backend.models.user_preferences import UserPreferences
from backend.models.article import NewsArticle
from backend.models.digest_log import DigestLog

from backend.services.email_service import send_digest_email
from backend.services.ranking_service import rank_articles
from backend.services.summary_service import summarize_article

logger = logging.getLogger(__name__)


async def send_digest_to_user(user_id: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )

        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"User not found: {user_id}")
            return

        if not user.is_active or not user.is_verified:
            logger.warning(f"User not allowed: {user.email}")
            return

        prefs_result = await db.execute(
            select(UserPreferences).where(
                UserPreferences.user_id == user.id
            )
        )

        prefs = prefs_result.scalar_one_or_none()

        sources = prefs.sources if prefs else []
        topics = prefs.topics if prefs else []
        top_n = prefs.top_n if prefs else 10
        email_enabled = prefs.email_enabled if prefs else True

        if not email_enabled:
            logger.info(f"Email disabled for {user.email}")
            return

        history_result = await db.execute(
            select(DigestLog).where(
                DigestLog.user_id == user.id,
                DigestLog.status == "sent",
            )
        )

        logs = history_result.scalars().all()

        sent_article_ids = set()

        for log in logs:
            if log.article_ids:
                sent_article_ids.update(log.article_ids)

        since = datetime.now(timezone.utc) - timedelta(days=3)

        filters = [
            NewsArticle.scraped_at >= since
        ]

        if sources:
            filters.append(
                NewsArticle.source.in_(sources)
            )

        result = await db.execute(
            select(NewsArticle)
            .where(and_(*filters))
            .order_by(desc(NewsArticle.final_rank_score))
            .limit(top_n * 10)
        )

        articles = result.scalars().all()

        if not articles:
            logger.warning(f"No recent articles for {user.email}")
            return

        ranked_articles = rank_articles(
            articles,
            user_topics=topics,
            user_sources=sources,
        )

        fresh_articles = [
            article
            for article in ranked_articles
            if str(article.id) not in sent_article_ids
        ]

        top_articles = fresh_articles[:top_n]

        if not top_articles:
            logger.warning(f"No new articles to send for {user.email}")
            return

        article_dicts = []

        for index, article in enumerate(top_articles):
            short_summary = summarize_article(
                article.title,
                article.summary or article.title,
            )

            article_dicts.append({
                "rank": index + 1,
                "personalized_score": getattr(
                    article,
                    "personalized_score",
                    article.final_rank_score or 0,
                ),
                "id": str(article.id),
                "title": article.title,
                "url": article.url,
                "summary": short_summary,
                "source": article.source,
                "source_name": article.source_name,
                "topics": article.topics,
                "published_at": (
                    article.published_at.isoformat()
                    if article.published_at
                    else None
                ),
            })

        log = DigestLog(
            user_id=user.id,
            article_ids=[
                str(article.id)
                for article in top_articles
            ],
            status="sending",
        )

        db.add(log)
        await db.commit()

        try:
            await send_digest_email(
                user.email,
                article_dicts,
            )

            log.status = "sent"

            logger.info(
                f"Digest sent to {user.email} "
                f"with {len(top_articles)} articles"
            )

        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)

            logger.error(
                f"Failed sending digest to {user.email}: {e}"
            )

        await db.commit()


async def send_daily_digests():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.is_active == True)
        )

        users = result.scalars().all()

    logger.info(f"Sending digests to {len(users)} users")

    for user in users:
        try:
            await send_digest_to_user(str(user.id))
        except Exception as e:
            logger.error(
                f"Error sending digest to {user.email}: {e}"
            )