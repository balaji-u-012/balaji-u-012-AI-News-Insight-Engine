"""
Email service — sends verification emails and daily digest emails.
Read More opens direct original article links only.
"""

import os
import smtplib
import logging
import asyncio
import html as html_escape

from groq import Groq
from pathlib import Path
from dotenv import load_dotenv

from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

FROM_EMAIL = os.getenv(
    "FROM_EMAIL",
    f"AI Digest <{SMTP_USER}>",
)

APP_URL = os.getenv(
    "APP_URL",
    "http://localhost:5173",
)

if not SMTP_USER or not SMTP_PASS:
    raise RuntimeError("SMTP credentials missing")


def get_original_url(article: dict) -> str:
    url_fields = [
        "url",
        "link",
        "article_url",
        "source_url",
        "original_url",
        "web_url",
        "html_url",
        "direct_url",
        "canonical_url",
        "youtube_url",
        "video_url",
        "reddit_url",
        "permalink",
        "href",
        "source_link",
        "external_url",
    ]

    for key in url_fields:
        value = article.get(key)

        if not value:
            continue

        value = str(value).strip()

        if (
            not value
            or value.lower() in ["none", "null", "#"]
        ):
            continue

        if value.startswith(("http://", "https://")):
            return value

        if value.startswith("www."):
            return "https://" + value

        if key == "permalink" and value.startswith("/"):
            return "https://www.reddit.com" + value

        if "." in value and " " not in value:
            return "https://" + value

    print(
        "⚠️ No valid URL found for:",
        article.get("title", "Unknown"),
    )

    return "#"


def _send_email_sync(
    to: str,
    subject: str,
    html: str,
    text: str = "",
):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to

    if text:
        msg.attach(MIMEText(text, "plain"))

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT,
    ) as server:
        server.ehlo()
        server.starttls()
        server.login(
            SMTP_USER,
            SMTP_PASS,
        )
        server.sendmail(
            SMTP_USER,
            to,
            msg.as_string(),
        )

    print(f"✅ Email sent to {to}")


async def send_email(
    to: str,
    subject: str,
    html: str,
    text: str = "",
):
    try:
        await asyncio.to_thread(
            _send_email_sync,
            to,
            subject,
            html,
            text,
        )

        logger.info(
            f"Email sent to {to}: {subject}"
        )

    except Exception as e:
        logger.error(
            f"Failed to send email: {e}"
        )
        raise


def shorten_title_with_groq(title: str) -> str:
    if not GROQ_API_KEY:
        return (
            title[:80] + "..."
            if len(title) > 80
            else title
        )

    try:
        client = Groq(
            api_key=GROQ_API_KEY,
        )

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Shorten this AI news title "
                        "for a premium email digest. "
                        "Keep it professional, clean "
                        "and under 8 words. "
                        "Return ONLY the title."
                    ),
                },
                {
                    "role": "user",
                    "content": title,
                },
            ],
            temperature=0.2,
            max_tokens=24,
        )

        return (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

    except Exception as e:
        logger.warning(
            f"Groq title shortening failed: {e}"
        )

        return (
            title[:80] + "..."
            if len(title) > 80
            else title
        )


async def send_verification_email(
    email: str,
    token: str,
):
    verify_url = f"{APP_URL}/verify/{token}"

    html = f"""
    <div style="
        font-family:Arial,sans-serif;
        max-width:480px;
        margin:0 auto;
        padding:40px 24px;
    ">
      <h1>Verify your email</h1>

      <p>Welcome to AI Digest.</p>

      <a href="{verify_url}"
         style="
         display:inline-block;
         padding:12px 20px;
         background:#111827;
         color:#fff;
         border-radius:8px;
         text-decoration:none;
         ">
        Verify Email
      </a>

      <p style="
         color:#888;
         font-size:12px;
         margin-top:20px;
      ">
        If you didn’t sign up,
        ignore this email.
      </p>
    </div>
    """

    await send_email(
        email,
        "Verify your AI Digest account",
        html,
        "Verify your AI Digest account",
    )


async def send_digest_email(
    email: str,
    articles: list[dict],
    user_id: str = "",
    date_str: str = None,
):
    if not date_str:
        date_str = datetime.now(
            timezone.utc
        ).strftime("%B %d, %Y")

    article_html = ""

    text_lines = [
        f"AI Digest — {date_str}",
        "",
    ]

    for i, article in enumerate(
        articles,
        start=1,
    ):
        raw_title = str(
            article.get("title")
            or "Untitled article"
        )

        short_title = shorten_title_with_groq(
            raw_title
        )

        title = html_escape.escape(
            short_title
        )

        description = (
            article.get("summary")
            or article.get("description")
            or article.get("content")
            or "No description available."
        )

        description = html_escape.escape(
            str(description)
        )

        if len(description) > 260:
            description = description[:260] + "..."

        direct_url = get_original_url(article)

        print(
            f"🔗 Article {i}: {short_title}"
        )
        print(
            f"   Direct URL: {direct_url}"
        )

        if direct_url == "#":
            print("   ⚠️ Skipped: no direct URL")
            continue

        safe_url = html_escape.escape(
            direct_url,
            quote=True,
        )

        source_name = html_escape.escape(
            str(
                article.get("source_name")
                or article.get("source")
                or "Unknown source"
            )
        )

        source_badge = f"""
        <span style="
            background:#111827;
            padding:5px 11px;
            border-radius:999px;
            font-size:11px;
            color:#ffffff;
            font-weight:700;
            margin-right:6px;
            display:inline-block;
            letter-spacing:0.03em;
        ">
            {source_name}
        </span>
        """

        article_html += f"""
        <div style="
            padding:24px 0;
            border-bottom:1px solid #eee9df;
        ">
          <div style="
             font-size:12px;
             color:#8a7f70;
             font-weight:700;
             letter-spacing:0.08em;
             text-transform:uppercase;
             margin-bottom:10px;
          ">
             Article #{i}
          </div>

          <h3 style="
              margin:6px 0 10px 0;
              font-size:21px;
              line-height:1.35;
              color:#111827;
              font-weight:800;
              letter-spacing:-0.02em;
          ">
            {title}
          </h3>

          <div style="margin:10px 0 14px 0;">
            {source_badge}
          </div>

          <p style="
             color:#4b5563;
             font-size:15px;
             line-height:1.75;
             margin:12px 0 18px 0;
          ">
            {description}
          </p>

          <a href="{safe_url}"
             target="_blank"
             rel="noopener noreferrer"
             style="
             display:inline-block;
             padding:12px 18px;
             background:#111827;
             color:#ffffff;
             border-radius:12px;
             text-decoration:none;
             font-size:14px;
             font-weight:700;
             ">
            Read Original Article →
          </a>

          <p style="
             font-size:11px;
             color:#9ca3af;
             margin-top:12px;
             word-break:break-all;
          ">
            {safe_url}
          </p>
        </div>
        """

        text_lines.extend(
            [
                f"{i}. {short_title}",
                f"Source: {source_name}",
                f"Description: {description}",
                f"Read original: {direct_url}",
                "",
            ]
        )

    if not article_html:
        print(
            f"❌ No valid article URLs found for {email}"
        )
        return

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport"
            content="width=device-width, initial-scale=1.0">
      <title>AI Digest - {date_str}</title>
    </head>

    <body style="
        margin:0;
        font-family:Arial,Helvetica,sans-serif;
        background:#f7f3eb;
        padding:28px 14px;
    ">
      <div style="
          max-width:680px;
          margin:auto;
          background:#ffffff;
          border-radius:26px;
          border:1px solid #eee9df;
          overflow:hidden;
          box-shadow:
          0 18px 50px rgba(17,24,39,0.08);
      ">

        <div style="
            padding:34px 34px 28px 34px;
            background:
            linear-gradient(
              135deg,
              #fffdf8,
              #ffffff,
              #f8f4ec
            );
            border-bottom:
            1px solid #eee9df;
        ">

          <div style="
              display:inline-block;
              padding:8px 13px;
              border-radius:999px;
              background:#111827;
              color:#ffffff;
              font-size:11px;
              font-weight:800;
              letter-spacing:0.12em;
              margin-bottom:18px;
          ">
            AI DIGEST
          </div>

          <h1 style="
              margin:0;
              color:#111827;
              font-size:32px;
              line-height:1.12;
              letter-spacing:-0.04em;
              font-weight:900;
          ">
            Your AI Intelligence Brief
          </h1>

          <p style="
              color:#6b7280;
              margin:14px 0 0 0;
              font-size:15px;
              line-height:1.7;
          ">
            Curated AI updates for {date_str}
          </p>
        </div>

        <div style="
            padding:6px 34px 10px 34px;
        ">
          {article_html}
        </div>

        <div style="
            text-align:center;
            padding:28px 34px 34px 34px;
            font-size:13px;
            color:#6b7280;
        ">
          <p style="
             margin:0 0 14px 0;
          ">
            You received this because
            you subscribed to AI Digest.
          </p>
        </div>
      </div>
    </body>
    </html>
    """

    await send_email(
        email,
        f"AI Digest — {date_str}",
        html,
        "\n".join(text_lines),
    )