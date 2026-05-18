import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from backend.core.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title = Column(String, nullable=False)

    url = Column(String, unique=True, nullable=False)

    summary = Column(Text)

    source = Column(String, nullable=False)

    source_name = Column(String)

    author = Column(String)

    published_at = Column(DateTime(timezone=True), nullable=True)

    scraped_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    topics = Column(ARRAY(String), default=[])

    thumbnail_url = Column(String)

    view_count = Column(Integer, default=0)

    like_count = Column(Integer, default=0)

    comment_count = Column(Integer, default=0)

    relevance_score = Column(Float, default=0)

    engagement_score = Column(Float, default=0)

    final_rank_score = Column(Float, default=0)