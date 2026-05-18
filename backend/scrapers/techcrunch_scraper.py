"""
TechCrunch AI scraper
"""

import logging
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import httpx

from backend.services.ranking_service import detect_topics

logger = logging.getLogger(__name__)

SOURCE = "techcrunch"
SOURCE_NAME = "TechCrunch"

RSS_URL = "https://techcrunch.com/category/artificial-intelligence/feed/"

NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "media": "http://search.yahoo.com/mrss/",
}


def clean_html(text: str | None, limit: int = 400) -> str | None:
    if not text:
        return None

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text[:limit] if text else None


async def scrape_techcrunch() -> list[dict]:
    articles: list[dict] = []

    try:
        async with httpx.AsyncClient(
            timeout=20,
            follow_redirects=True,
            headers={
                "User-Agent": "AIDigestBot/1.0",
                "Accept": "application/rss+xml, application/xml, text/xml",
            },
        ) as client:
            response = await client.get(RSS_URL)
            response.raise_for_status()

        root = ET.fromstring(response.content)
        channel = root.find("channel")

        if channel is None:
            logger.warning("TechCrunch RSS missing channel")
            return []

        for item in channel.findall("item")[:20]:
            title = (item.findtext("title") or "").strip()
            url = (item.findtext("link") or "").strip()

            if not title or not url:
                continue

            summary = clean_html(item.findtext("description"))

            author = item.findtext("dc:creator", namespaces=NS)

            published_at = None
            pub_date = item.findtext("pubDate")

            if pub_date:
                try:
                    published_at = parsedate_to_datetime(pub_date)
                except Exception:
                    logger.warning("Invalid TechCrunch date: %s", pub_date)

            thumbnail = None

            media = item.find("media:content", NS)

            if media is not None and media.get("url"):
                thumbnail = media.get("url")

            if not thumbnail:
                enclosure = item.find("enclosure")

                if enclosure is not None:
                    content_type = enclosure.get("type", "")

                    if content_type.startswith("image"):
                        thumbnail = enclosure.get("url")

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
                    "author": author,
                    "published_at": published_at,
                    "topics": topics,
                    "thumbnail_url": thumbnail,
                }
            )

        logger.info("TechCrunch scraper found %s articles", len(articles))

        return articles

    except Exception as e:
        logger.error("TechCrunch scraper error: %s", e)
        return []