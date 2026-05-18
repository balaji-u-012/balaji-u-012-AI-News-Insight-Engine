# backend/services/scheduler.py

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


# =========================================================
# Start Scheduler
# =========================================================

async def start_scheduler():

    # Import here to avoid circular imports
    from backend.services.scraper_service import (
        run_all_scrapers,
    )

    from backend.services.digest_service import (
        send_daily_digests,
    )

    scheduler = AsyncIOScheduler()

    # =====================================================
    # Scrape Articles Every 6 Hours
    # =====================================================

    scheduler.add_job(
        run_all_scrapers,
        CronTrigger(hour="*/6"),
        id="scrape_all",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # =====================================================
    # Send Daily Digests at 08:00 UTC
    # =====================================================

    scheduler.add_job(
        send_daily_digests,
        CronTrigger(hour=8, minute=0),
        id="send_digests",
        replace_existing=True,
        misfire_grace_time=300,
    )

    scheduler.start()

    logger.info(
        "✅ Scheduler started successfully"
    )

    return scheduler


# =========================================================
# Stop Scheduler
# =========================================================

async def stop_scheduler(scheduler):

    if scheduler and scheduler.running:

        scheduler.shutdown(wait=False)

        logger.info(
            "🛑 Scheduler stopped"
        )