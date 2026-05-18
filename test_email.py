import asyncio

from backend.services.email_service import send_email


async def main():
    await send_email(
        to="balajiumashanker1@gmail.com",
        subject="AI Digest SMTP Test",
        html="<h1>Email working</h1><p>SMTP is configured correctly.</p>",
        text="Email working",
    )


asyncio.run(main())