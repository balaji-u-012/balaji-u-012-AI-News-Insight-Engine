from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user_preferences import UserPreferences
from backend.models.user_event import UserEvent
from backend.models.article import NewsArticle


EVENT_WEIGHTS = {
    "click": 1,
    "like": 4,
    "save": 5,
    "dismiss": -3,
}


async def update_user_preferences_from_events(
    user_id,
    db: AsyncSession,
):
    result = await db.execute(
        select(UserEvent, NewsArticle)
        .join(NewsArticle, UserEvent.article_id == NewsArticle.id)
        .where(UserEvent.user_id == user_id)
        .order_by(UserEvent.created_at.desc())
        .limit(100)
    )

    rows = result.all()

    topic_scores = defaultdict(float)
    source_scores = defaultdict(float)

    for event, article in rows:
        weight = EVENT_WEIGHTS.get(event.event_type, 0)

        for topic in article.topics or []:
            topic_scores[topic] += weight

        if article.source:
            source_scores[article.source] += weight

    best_topics = [
        topic
        for topic, score in sorted(
            topic_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        if score > 0
    ][:5]

    best_sources = [
        source
        for source, score in sorted(
            source_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        if score > 0
    ][:3]

    prefs_result = await db.execute(
        select(UserPreferences).where(
            UserPreferences.user_id == user_id
        )
    )

    prefs = prefs_result.scalar_one_or_none()

    if not prefs:
        prefs = UserPreferences(user_id=user_id)
        db.add(prefs)

    if best_topics:
        prefs.topics = best_topics

    if best_sources:
        prefs.sources = best_sources

    await db.commit()

    return prefs