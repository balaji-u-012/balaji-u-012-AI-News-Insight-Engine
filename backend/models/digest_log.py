import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from backend.core.database import Base


class DigestLog(Base):
    __tablename__ = "digest_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id = Column(
        UUID(as_uuid=True),
        index=True,
        nullable=False,
    )

    article_ids = Column(
        JSON,
        default=list,
    )

    status = Column(
        String,
        default="sent",
    )

    error_message = Column(
        String,
        nullable=True,
    )

    sent_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )