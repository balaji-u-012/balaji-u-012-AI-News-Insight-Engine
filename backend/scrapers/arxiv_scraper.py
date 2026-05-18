"""
ArXiv scraper
"""

import asyncio
import logging
from datetime import datetime
import xml.etree.ElementTree as ET

import httpx

from backend.services.ranking_service import detect_topics

logger = logging.getLogger(__name__)

SOURCE = "arxiv"
SOURCE_NAME = "ArXiv"

ARXIV_API = "https://export.arxiv.org/api/query"

QUERIES = [
    "cat:cs.AI",
    "cat:cs.LG",
    "cat:cs.CL",
]

NS = {
    "atom": "http://www.w3.org/2005/Atom",
}


async def fetch_arxiv_query(
    client: httpx.AsyncClient,
    query: str,
    max_results: int = 5,
) -> list[dict]:

    articles = []

    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    try:

        response = await client.get(
            ARXIV_API,
            params=params,
        )

        response.raise_for_status()

        root = ET.fromstring(response.content)

        for entry in root.findall(
            "atom:entry",
            NS
        ):

            title = (
                entry.findtext(
                    "atom:title",
                    namespaces=NS
                ) or ""
            ).replace("\n", " ").strip()

            url = (
                entry.findtext(
                    "atom:id",
                    namespaces=NS
                ) or ""
            )

            summary = (
                entry.findtext(
                    "atom:summary",
                    namespaces=NS
                ) or ""
            ).replace("\n", " ").strip()

            published_str = (
                entry.findtext(
                    "atom:published",
                    namespaces=NS
                ) or ""
            )

            published_at = None

            if published_str:
                try:
                    published_at = datetime.fromisoformat(
                        published_str.replace(
                            "Z",
                            "+00:00"
                        )
                    )
                except Exception:
                    pass

            authors = []

            for author in entry.findall(
                "atom:author",
                NS
            ):
                name = author.findtext(
                    "atom:name",
                    namespaces=NS
                )

                if name:
                    authors.append(name)

            author_text = ", ".join(authors[:3])

            topics = detect_topics(
                f"{title} {summary}"
            )

            if "research" not in topics:
                topics.append("research")

            articles.append({
                "title": title,
                "url": url,
                "summary": summary[:500],
                "source": SOURCE,
                "source_name": SOURCE_NAME,
                "author": author_text,
                "published_at": published_at,
                "topics": topics,
                "thumbnail_url": None,
            })

        logger.info(
            f"ArXiv query {query}: "
            f"{len(articles)} papers"
        )

        return articles

    except Exception as e:

        logger.warning(
            f"ArXiv query {query} error: {e}"
        )

        return []


async def scrape_arxiv() -> list[dict]:

    all_articles = []

    try:

        async with httpx.AsyncClient(
            timeout=30,
            headers={
                "User-Agent": "ai-digest/1.0"
            },
        ) as client:

            for query in QUERIES:

                results = await fetch_arxiv_query(
                    client,
                    query,
                    max_results=5,
                )

                all_articles.extend(results)

                await asyncio.sleep(5)

        seen = set()

        unique_articles = []

        for article in all_articles:

            if article["url"] in seen:
                continue

            seen.add(article["url"])

            unique_articles.append(article)

        logger.info(
            f"ArXiv scraper found "
            f"{len(unique_articles)} papers"
        )

        return unique_articles[:15]

    except Exception as e:

        logger.error(
            f"ArXiv scraper error: {e}"
        )

        return []