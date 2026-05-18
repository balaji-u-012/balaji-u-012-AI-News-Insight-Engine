# backend/models/user_preferences.py

import uuid

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from backend.core.database import Base


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    topics = Column(ARRAY(String), default=[])

    sources = Column(ARRAY(String), default=[])

    digest_frequency = Column(String, default="daily")

    digest_time = Column(String, default="08:00")

    top_n = Column(Integer, default=10)

    email_enabled = Column(Boolean, default=True)