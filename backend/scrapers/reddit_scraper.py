"""
Reddit scraper
"""

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from backend.services.ranking_service import detect_topics

logger = logging.getLogger(__name__)

SOURCE = "reddit"

SUBREDDITS = [
    "MachineLearning",
    "artificial",
    "LocalLLaMA",
    "singularity",
    "OpenAI",
]


async def scrape_subreddit(
    client: httpx.AsyncClient,
    subreddit: str,
) -> list[dict]:

    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"

    articles = []

    try:

        response = await client.get(url)
        response.raise_for_status()

        data = response.json()

        posts = (
            data.get("data", {})
            .get("children", [])
        )

        for post in posts:

            p = post.get("data", {})

            if p.get("removed_by_category"):
                continue

            title = (
                p.get("title", "")
                .strip()
            )

            if not title or len(title) < 10:
                continue

            selftext = (
                p.get("selftext", "")
                .replace("\n", " ")
                .strip()
            )

            if p.get("is_self") and not selftext:
                continue

            article_url = p.get("url", "")

            if (
                not article_url
                or "reddit.com" in article_url
            ):
                article_url = (
                    "https://www.reddit.com"
                    f"{p.get('permalink', '')}"
                )

            summary = (
                selftext[:300]
                if selftext
                else None
            )

            published_at = datetime.fromtimestamp(
                p.get("created_utc", 0),
                tz=timezone.utc,
            )

            thumbnail = None

            thumb = p.get("thumbnail", "")

            if thumb.startswith("http"):
                thumbnail = thumb

            topics = detect_topics(
                f"{title} {summary or ''}"
            )

            if "community" not in topics:
                topics.append("community")

            articles.append({
                "title": title,
                "url": article_url,
                "summary": summary,
                "source": SOURCE,
                "source_name": f"r/{subreddit}",
                "author": p.get("author"),
                "published_at": published_at,
                "topics": topics,
                "thumbnail_url": thumbnail,
                "like_count": p.get("ups", 0),
                "comment_count": p.get(
                    "num_comments",
                    0
                ),
            })

        logger.info(
            f"Reddit r/{subreddit} found "
            f"{len(articles)} posts"
        )

        return articles

    except Exception as e:

        logger.warning(
            f"Reddit r/{subreddit} error: {e}"
        )

        return []


async def scrape_reddit() -> list[dict]:

    all_articles = []

    headers = {
        "User-Agent": (
            "AIDigestBot/1.0 "
            "by u/ai_digest_bot"
        )
    }

    try:

        async with httpx.AsyncClient(
            timeout=20,
            headers=headers,
            follow_redirects=True,
        ) as client:

            tasks = [
                scrape_subreddit(
                    client,
                    subreddit
                )
                for subreddit in SUBREDDITS
            ]

            results = await asyncio.gather(
                *tasks
            )

        for articles in results:
            all_articles.extend(articles)

        seen_urls = set()
        unique_articles = []

        for article in all_articles:

            url = article.get("url")

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            unique_articles.append(article)

        unique_articles.sort(
            key=lambda article: (
                article.get("like_count", 0)
                + article.get("comment_count", 0)
            ),
            reverse=True,
        )

        logger.info(
            f"Reddit scraper found "
            f"{len(unique_articles)} unique posts"
        )

        return unique_articles[:30]

    except Exception as e:

        logger.error(
            f"Reddit scraper error: {e}"
        )

        return []