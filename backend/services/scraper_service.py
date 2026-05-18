"""
Scraper service — runs all source scrapers and persists results.

Each scraper returns a list of dicts with keys:
    title
    url
    summary
    source
    source_name
    published_at
    topics
    thumbnail_url
    view_count
    like_count
    comment_count
"""

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import AsyncSessionLocal

from backend.models.article import NewsArticle
from backend.models.scraper_run import ScraperRun

from backend.scrapers.anthropic_scraper import scrape_anthropic
from backend.scrapers.openai_scraper import scrape_openai
from backend.scrapers.youtube_scraper import scrape_youtube
from backend.scrapers.reddit_scraper import scrape_reddit
from backend.scrapers.techcrunch_scraper import scrape_techcrunch
from backend.scrapers.arxiv_scraper import scrape_arxiv

from backend.services.ranking_service import score_article


logger = logging.getLogger(__name__)


# =========================================================
# Registered Scrapers
# =========================================================

SCRAPERS = {
    "anthropic": scrape_anthropic,
    "openai": scrape_openai,
    "youtube": scrape_youtube,
    "reddit": scrape_reddit,
    "techcrunch": scrape_techcrunch,
    "arxiv": scrape_arxiv,
}


# =========================================================
# Run Single Scraper
# =========================================================

async def run_scraper(
    source: str,
    scraper_fn
) -> list[dict]:
    """
    Run a single scraper safely.
    """

    try:

        logger.info(f"Starting scraper: {source}")

        articles = await scraper_fn()

        logger.info(
            f"Scraper {source} found {len(articles)} articles"
        )

        return articles

    except Exception as e:

        logger.error(
            f"Scraper {source} failed: {e}"
        )

        return []


# =========================================================
# Save Articles
# =========================================================

async def save_articles(
    db: AsyncSession,
    articles: list[dict],
    source: str
) -> int:
    """
    Save articles to database.
    Skips duplicate URLs.
    """

    saved_count = 0

    for raw in articles:

        try:

            # -----------------------------------------
            # Check Duplicate URL
            # -----------------------------------------

            result = await db.execute(
                select(NewsArticle).where(
                    NewsArticle.url == raw["url"]
                )
            )

            existing = result.scalar_one_or_none()

            if existing:
                continue

            # -----------------------------------------
            # Score Article
            # -----------------------------------------

            relevance_score, engagement_score, final_score = (
                score_article(raw)
            )

            # -----------------------------------------
            # Create Model
            # -----------------------------------------

            article = NewsArticle(
                title=raw["title"],
                url=raw["url"],
                summary=raw.get("summary"),

                source=raw["source"],
                source_name=raw["source_name"],

                author=raw.get("author"),

                published_at=raw.get("published_at"),

                topics=raw.get("topics", []),

                thumbnail_url=raw.get("thumbnail_url"),

                view_count=raw.get("view_count"),
                like_count=raw.get("like_count"),
                comment_count=raw.get("comment_count"),

                relevance_score=relevance_score,
                engagement_score=engagement_score,
                final_rank_score=final_score,
            )

            db.add(article)

            saved_count += 1

        except Exception as e:

            logger.warning(
                f"Failed to save article {raw.get('url')}: {e}"
            )

            continue

    # -----------------------------------------
    # Commit
    # -----------------------------------------

    if saved_count:
        await db.commit()

    return saved_count


# =========================================================
# Run All Scrapers
# =========================================================

async def run_all_scrapers(
    db: AsyncSession = None
):
    """
    Run all scrapers concurrently
    and save results.
    """

    close_db = False

    # Create DB session if not provided

    if db is None:

        db = AsyncSessionLocal()

        close_db = True

    try:

        # -----------------------------------------
        # Prepare Tasks
        # -----------------------------------------

        tasks = [
            (source, scraper_fn)
            for source, scraper_fn
            in SCRAPERS.items()
        ]

        # -----------------------------------------
        # Run Concurrently
        # -----------------------------------------

        results = await asyncio.gather(
            *[
                run_scraper(source, scraper_fn)
                for source, scraper_fn in tasks
            ],
            return_exceptions=True
        )

        # -----------------------------------------
        # Save Results
        # -----------------------------------------

        for (source, _), articles in zip(tasks, results):

            # -------------------------------------
            # Success
            # -------------------------------------

            if isinstance(articles, list):

                run_log = ScraperRun(
                    source=source,
                    articles_found=len(articles),
                    articles_saved=0,
                    status="running",
                    started_at=datetime.utcnow(),
                )

                db.add(run_log)

                await db.flush()

                saved_count = await save_articles(
                    db,
                    articles,
                    source
                )

                run_log.articles_saved = saved_count
                run_log.status = "success"
                run_log.finished_at = datetime.utcnow()

                await db.commit()

                logger.info(
                    f"{source}: saved "
                    f"{saved_count}/{len(articles)} articles"
                )

            # -------------------------------------
            # Failure
            # -------------------------------------

            else:

                logger.error(
                    f"Scraper {source} returned error: {articles}"
                )

    finally:

        if close_db:
            await db.close()
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def main():
        async with AsyncSessionLocal() as db:
            await run_all_scrapers(db)

    asyncio.run(main())