"""
Anthropic blog scraper
"""

import logging
from datetime import datetime
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from backend.services.ranking_service import detect_topics

logger = logging.getLogger(__name__)

BASE_URL = "https://www.anthropic.com"
NEWS_URL = f"{BASE_URL}/news"

SOURCE = "anthropic"
SOURCE_NAME = "Anthropic"


async def scrape_anthropic() -> list[dict]:
    articles: list[dict] = []

    try:
        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/124 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml",
            },
        ) as client:
            response = await client.get(NEWS_URL)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        seen_urls: set[str] = set()

        for link in soup.find_all("a", href=True):
            href = link.get("href", "").strip()

            if not href.startswith("/news/"):
                continue

            if href == "/news":
                continue

            url = urljoin(BASE_URL, href)

            if url in seen_urls:
                continue

            seen_urls.add(url)

            title = link.get_text(" ", strip=True)

            if not title or len(title) < 10:
                continue

            summary = None
            paragraph = link.find("p")

            if paragraph:
                summary = paragraph.get_text(" ", strip=True)

            published_at = None
            time_el = link.find("time")

            if time_el:
                date_value = time_el.get("datetime")

                if date_value:
                    try:
                        published_at = datetime.fromisoformat(
                            date_value.replace("Z", "+00:00")
                        )
                    except Exception:
                        logger.warning("Invalid Anthropic date: %s", date_value)

            thumbnail = None
            img = link.find("img")

            if img:
                thumbnail = img.get("src") or img.get("data-src")

                if thumbnail:
                    thumbnail = urljoin(BASE_URL, thumbnail)

            topics = detect_topics(f"{title} {summary or ''}")

            if "news" not in topics:
                topics.append("news")

            articles.append(
                {
                    "title": title,
                    "url": url,
                    "summary": summary,
                    "source": SOURCE,
                    "source_name": SOURCE_NAME,
                    "published_at": published_at,
                    "topics": topics,
                    "thumbnail_url": thumbnail,
                }
            )

        logger.info("Anthropic scraper found %s articles", len(articles))

    except Exception as e:
        logger.error("Anthropic scraper error: %s", e)

    return articles[:20]