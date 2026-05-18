import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def summarize_article(
    title: str,
    content: str,
) -> str:
    """
    Generate short AI summary for digest emails.
    """

    if not content:
        return "No summary available."

    content = content[:4000]

    prompt = f"""
Summarize this AI news article in 2 short lines.

Rules:
- Keep it concise
- Mention the key update
- Mention why it matters
- Maximum 45 words
- Easy to read in email digest

Title:
{title}

Content:
{content}
"""

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI news summarizer."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
            max_tokens=120,
        )

        summary = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        return summary

    except Exception as e:

        print("Summary error:", e)

        return content[:180] + "..."