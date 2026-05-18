# backend/models/__init__.py
# backend/models/__init__.py

from backend.models.user import User
from backend.models.article import NewsArticle
from backend.models.user_preferences import UserPreferences
from backend.models.scraper_run import ScraperRun
from backend.models.digest_log import DigestLog

__all__ = [
    "User",
    "NewsArticle",
    "UserPreferences",
    "ScraperRun",
    "DigestLog",
]