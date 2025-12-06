import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import Settings

logger = logging.getLogger("ether.scheduler")

_scheduler: Optional[AsyncIOScheduler] = None


async def keepalive_tick():
    """Placeholder keepalive job.

    In the cloud, you can later extend this to ping Supabase, Render, etc.
    For now it just logs so you can see it firing without breaking anything.
    """
    logger.info("[SCHEDULER] keepalive tick")


async def ocr_tick():
    """Placeholder OCR queue processor.

    Ether v2 doesn't have a full OCR queue yet, so this is a stub that
    you can safely leave running.
    """
    logger.info("[SCHEDULER] OCR tick (no-op placeholder)")


async def metrics_tick():
    """Placeholder metrics/usage job.

    Later this can aggregate usage, token counts, etc.
    """
    logger.info("[SCHEDULER] metrics tick (no-op placeholder)")


def init_scheduler(settings: Settings) -> Optional[AsyncIOScheduler]:
    global _scheduler

    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler disabled via SCHEDULER_ENABLED env.")
        return None

    if _scheduler is not None:
        return _scheduler

    scheduler = AsyncIOScheduler(timezone="UTC")

    # Keepalive
    scheduler.add_job(
        keepalive_tick,
        IntervalTrigger(seconds=settings.KEEPALIVE_INTERVAL_SECONDS),
        id="keepalive",
        replace_existing=True,
    )

    # OCR queue placeholder
    scheduler.add_job(
        ocr_tick,
        IntervalTrigger(seconds=settings.OCR_INTERVAL_SECONDS),
        id="ocr",
        replace_existing=True,
    )

    # Metrics
    scheduler.add_job(
        metrics_tick,
        IntervalTrigger(seconds=settings.METRICS_INTERVAL_SECONDS),
        id="metrics",
        replace_existing=True,
    )

    scheduler.start()
    _scheduler = scheduler
    logger.info("Background scheduler started with jobs: %s", scheduler.get_jobs())
    return scheduler


def shutdown_scheduler():
    global _scheduler
    if _scheduler:
        logger.info("Shutting down background scheduler.")
        _scheduler.shutdown()
        _scheduler = None
