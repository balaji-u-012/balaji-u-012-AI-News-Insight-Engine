"""
OpenAI scraper using sitemap XML
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime

import httpx

from backend.services.ranking_service import detect_topics

logger = logging.getLogger(__name__)

SOURCE = "openai"
SOURCE_NAME = "OpenAI"

SITEMAPS = [
    "https://openai.com/sitemap.xml/company/",
    "https://openai.com/sitemap.xml/product/",
]

NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9"
}


def make_title(url: str) -> str:
    slug = url.rstrip("/").split("/")[-1]
    return slug.replace("-", " ").title()


async def scrape_openai() -> list[dict]:

    articles = []

    try:

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/xml,text/xml",
            },
        ) as client:

            for sitemap in SITEMAPS:

                response = await client.get(sitemap)
                response.raise_for_status()

                root = ET.fromstring(response.content)

                urls = root.findall(
                    "sm:url",
                    NS
                )

                for item in urls:

                    url = item.findtext(
                        "sm:loc",
                        namespaces=NS
                    )

                    if not url:
                        continue

                    if "/news/" not in url:
                        continue

                    title = make_title(url)

                    lastmod = item.findtext(
                        "sm:lastmod",
                        namespaces=NS
                    )

                    published_at = None

                    if lastmod:
                        try:
                            published_at = datetime.fromisoformat(
                                lastmod.replace(
                                    "Z",
                                    "+00:00"
                                )
                            )
                        except Exception:
                            pass

                    topics = detect_topics(title)

                    if "news" not in topics:
                        topics.append("news")

                    articles.append({
                        "title": title,
                        "url": url,
                        "summary": None,
                        "source": SOURCE,
                        "source_name": SOURCE_NAME,
                        "published_at": published_at,
                        "topics": topics,
                        "thumbnail_url": None,
                    })

        seen = set()
        unique_articles = []

        for article in articles:

            if article["url"] in seen:
                continue

            seen.add(article["url"])

            unique_articles.append(article)

        logger.info(
            "OpenAI scraper found %s articles",
            len(unique_articles)
        )

        return unique_articles[:20]

    except Exception as e:

        logger.error(
            "OpenAI scraper error: %s",
            e
        )

        return []


if __name__ == "__main__":

    import asyncio

    async def main():

        articles = await scrape_openai()

        print(f"Found {len(articles)} articles")

        for article in articles[:5]:
            print(article["title"])
            print(article["url"])
            print()

    asyncio.run(main())