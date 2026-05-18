"""
YouTube scraper — RSS feed version.
No YOUTUBE_API_KEY required.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
)

from backend.services.ranking_service import detect_topics

logger = logging.getLogger(__name__)

SOURCE = "youtube"
SOURCE_NAME = "YouTube"

AI_CHANNELS = [
    "UCbmNph6atAoGfqLoCL_duAg",
    "UCWX3yGbODI3hKP6gjhzRJcg",
    "UCZHmQk67mSJgfCCTn7xBfew",
    "UCnUYZLuoy1rq1aVMwx4aTzw",
    "UCbfYPyITQ-7l4upoX8nvctg",
    "UC0RhatS1pyxInC00YKjjBqQ",
]


def get_rss_url(channel_id: str) -> str:
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def extract_video_id(video_url: str) -> str:
    if "youtube.com/watch?v=" in video_url:
        return video_url.split("v=")[1].split("&")[0]

    if "youtu.be/" in video_url:
        return video_url.split("youtu.be/")[1].split("?")[0]

    if "youtube.com/shorts/" in video_url:
        return video_url.split("shorts/")[1].split("?")[0]

    return video_url


def get_transcript(video_id: str) -> Optional[str]:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)

        text = " ".join(
            item.get("text", "")
            for item in transcript
        )

        if not text:
            return None

        return text[:1500]

    except (TranscriptsDisabled, NoTranscriptFound):
        return None

    except Exception:
        return None


def fetch_channel_videos(
    channel_id: str,
    hours: int = 168,
) -> list[dict]:
    """
    Fetch recent videos from one YouTube channel RSS feed.
    """

    articles = []

    try:
        feed = feedparser.parse(
            get_rss_url(channel_id)
        )

        if not feed.entries:
            logger.warning(
                f"YouTube channel {channel_id}: no feed entries"
            )
            return []

        cutoff_time = (
            datetime.now(timezone.utc)
            - timedelta(hours=hours)
        )

        for entry in feed.entries:

            url = entry.get("link", "")

            if not url:
                continue

            if "/shorts/" in url:
                continue

            published_parsed = entry.get(
                "published_parsed"
            )

            if not published_parsed:
                continue

            published_at = datetime(
                *published_parsed[:6],
                tzinfo=timezone.utc
            )

            if published_at < cutoff_time:
                continue

            title = entry.get("title", "").strip()

            if not title:
                continue

            description = (
                entry.get("summary", "")
                .replace("\n", " ")
                .strip()
            )

            video_id = extract_video_id(url)

            transcript = get_transcript(video_id)

            summary_text = transcript or description

            topics = detect_topics(
                f"{title} {summary_text or ''}"
            )

            if "video" not in topics:
                topics.append("video")

            thumbnail = None

            media_thumbnail = entry.get(
                "media_thumbnail"
            )

            if (
                media_thumbnail
                and isinstance(media_thumbnail, list)
            ):
                thumbnail = media_thumbnail[0].get("url")

            channel_name = entry.get(
                "author",
                SOURCE_NAME
            )

            articles.append({
                "title": title,
                "url": url,
                "summary": (
                    summary_text[:500]
                    if summary_text
                    else None
                ),
                "source": SOURCE,
                "source_name": (
                    f"YouTube — {channel_name}"
                ),
                "author": channel_name,
                "published_at": published_at,
                "topics": topics,
                "thumbnail_url": thumbnail,
                "view_count": 0,
                "like_count": 0,
                "comment_count": 0,
            })

        logger.info(
            f"YouTube channel {channel_id}: "
            f"{len(articles)} videos"
        )

        return articles

    except Exception as e:
        logger.warning(
            f"YouTube channel {channel_id} error: {e}"
        )
        return []


async def scrape_youtube() -> list[dict]:
    """
    Scrape AI YouTube videos from RSS feeds.
    """

    all_articles = []

    try:
        tasks = [
            asyncio.to_thread(
                fetch_channel_videos,
                channel_id,
                168,
            )
            for channel_id in AI_CHANNELS
        ]

        results = await asyncio.gather(*tasks)

        for videos in results:
            all_articles.extend(videos)

        seen = set()
        unique_articles = []

        for article in all_articles:

            url = article.get("url")

            if not url:
                continue

            if url in seen:
                continue

            seen.add(url)

            unique_articles.append(article)

        unique_articles.sort(
            key=lambda article: (
                article.get("published_at")
                or datetime.min.replace(tzinfo=timezone.utc)
            ),
            reverse=True
        )

        logger.info(
            f"YouTube scraper found "
            f"{len(unique_articles)} videos"
        )

        return unique_articles[:20]

    except Exception as e:
        logger.error(
            f"YouTube scraper error: {e}"
        )
        return []