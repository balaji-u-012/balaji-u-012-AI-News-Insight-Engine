import math
from datetime import datetime, timezone

from backend.models.article import NewsArticle


AI_KEYWORDS = [
    "llm", "large language model", "gpt", "claude", "gemini",
    "mistral", "transformer", "neural network", "deep learning",
    "machine learning", "artificial intelligence", "generative ai",
    "foundation model", "reinforcement learning", "fine-tuning",
    "rlhf", "diffusion model", "computer vision", "nlp",
    "natural language processing", "openai", "anthropic",
    "google deepmind", "meta ai", "hugging face", "ai safety",
    "alignment", "multimodal", "agent", "rag", "vector",
    "embedding", "inference", "training", "benchmark", "evaluation",
]


TOPIC_KEYWORDS = {
    "llm": ["llm", "large language model", "gpt", "claude", "gemini", "mistral", "chatgpt"],
    "computer-vision": ["computer vision", "image recognition", "diffusion", "stable diffusion", "dall-e", "midjourney"],
    "robotics": ["robot", "robotics", "autonomous", "humanoid", "manipulation"],
    "ai-safety": ["safety", "alignment", "hallucination", "bias", "ethics", "risk", "rlhf"],
    "open-source": ["open source", "open-source", "hugging face", "llama", "mistral", "ollama"],
    "research": ["paper", "arxiv", "research", "study", "benchmark", "evaluation"],
    "industry": ["openai", "anthropic", "google", "microsoft", "meta", "amazon", "startup", "funding"],
    "policy": ["regulation", "policy", "government", "law", "congress", "eu ai act", "compliance"],
}


SOURCE_AUTHORITY = {
    "anthropic": 1.0,
    "openai": 0.95,
    "arxiv": 0.90,
    "techcrunch": 0.80,
    "youtube": 0.70,
    "reddit": 0.60,
}


def detect_topics(text: str) -> list[str]:
    if not text:
        return []

    text_lower = text.lower()
    detected_topics = []

    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            detected_topics.append(topic)

    return detected_topics


def compute_relevance(raw: dict) -> float:
    text = f"""
    {raw.get("title", "")}
    {raw.get("summary", "")}
    """.lower()

    matched_keywords = sum(
        1 for keyword in AI_KEYWORDS
        if keyword in text
    )

    keyword_score = min(matched_keywords / 5.0, 1.0)

    recency_score = 0.5
    published_at = raw.get("published_at")

    if published_at:
        if isinstance(published_at, str):
            try:
                published_at = datetime.fromisoformat(
                    published_at.replace("Z", "+00:00")
                )
            except Exception:
                published_at = None

        if published_at:
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)

            age_hours = max(
                0,
                (now - published_at).total_seconds() / 3600,
            )

            recency_score = math.exp(-age_hours / (24 * 3.5))

    authority_score = SOURCE_AUTHORITY.get(
        raw.get("source", ""),
        0.5,
    )

    relevance = (
        0.4 * keyword_score
        + 0.3 * recency_score
        + 0.3 * authority_score
    )

    return round(relevance, 4)


def compute_engagement(raw: dict) -> float:
    views = raw.get("view_count") or 0
    likes = raw.get("like_count") or 0
    comments = raw.get("comment_count") or 0

    if not any([views, likes, comments]):
        return 0.3

    view_score = math.log1p(views) / math.log1p(1_000_000)
    like_score = math.log1p(likes) / math.log1p(50_000)
    comment_score = math.log1p(comments) / math.log1p(5_000)

    engagement = (
        0.4 * view_score
        + 0.4 * like_score
        + 0.2 * comment_score
    )

    return round(min(engagement, 1.0), 4)


def score_article(raw: dict) -> tuple[float, float, float]:
    relevance = compute_relevance(raw)
    engagement = compute_engagement(raw)

    final_score = (
        0.6 * relevance
        + 0.4 * engagement
    )

    return (
        round(relevance, 4),
        round(engagement, 4),
        round(final_score, 4),
    )


def rank_articles(
    articles: list[NewsArticle],
    user_topics: list[str] = None,
    user_sources: list[str] = None,
) -> list[NewsArticle]:
    if not articles:
        return []

    user_topics = user_topics or []
    user_sources = user_sources or []

    ranked = []

    for article in articles:
        base_score = article.final_rank_score or 0

        article_topics = set(article.topics or [])
        preferred_topics = set(user_topics)

        topic_overlap = len(
            article_topics.intersection(preferred_topics)
        )

        topic_score = min(topic_overlap * 0.10, 0.40)

        source_score = 0.0
        if user_sources and article.source in user_sources:
            source_score = 0.15

        freshness_score = 0.0

        if article.published_at:
            try:
                published = article.published_at

                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)

                now = datetime.now(timezone.utc)

                age_hours = max(
                    0,
                    (now - published).total_seconds() / 3600,
                )

                freshness_score = max(
                    0,
                    0.20 - (age_hours / 500),
                )

            except Exception:
                freshness_score = 0.0

        personalized_score = (
            base_score
            + topic_score
            + source_score
            + freshness_score
        )

        article.personalized_score = round(personalized_score, 4)

        ranked.append(article)

    ranked.sort(
        key=lambda item: item.personalized_score,
        reverse=True,
    )

    return ranked