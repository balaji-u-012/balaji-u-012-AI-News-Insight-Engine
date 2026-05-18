import asyncio
from backend.services.email_service import send_digest_email

articles = [
    {
        "title": "OpenAI co-founder Greg Brockman takes charge of product strategy",
        "summary": "OpenAI is reportedly changing product strategy and combining ChatGPT with Codex.",
        "url": "https://techcrunch.com/",
        "source_name": "TechCrunch",
        "topics": ["llm", "industry", "news"]
    },
    {
        "title": "Introducing Claude Design by Anthropic Labs",
        "summary": "Claude Design helps users create visual work like designs, prototypes, slides, and one-pagers.",
        "url": "https://www.anthropic.com/",
        "source_name": "Anthropic",
        "topics": ["llm", "design"]
    }
]

async def main():
    await send_digest_email(
        "balajiumashanker@gmail.com",
        articles
    )
    print("✅ Digest email sent")

asyncio.run(main())