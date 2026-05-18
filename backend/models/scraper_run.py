# backend/models/scraper_run.py

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID

from backend.core.database import Base


class ScraperRun(Base):
    __tablename__ = "scraper_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    source = Column(String, nullable=False)

    articles_found = Column(Integer, default=0)

    articles_saved = Column(Integer, default=0)

    status = Column(String, default="running")

    started_at = Column(DateTime, default=datetime.utcnow)

    finished_at = Column(DateTime)