import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.services.keepalive import run_keepalive
from app.services.ocr import run_ocr_tick
from app.services.metrics import run_metrics_tick

logger = logging.getLogger("ether.scheduler")

_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        settings = get_settings()
        _scheduler = BackgroundScheduler(timezone="UTC")
        _scheduler.add_job(
            run_keepalive,
            "interval",
            seconds=settings.KEEPALIVE_INTERVAL_SECONDS,
            id="keepalive",
            replace_existing=True,
        )
        _scheduler.add_job(
            run_ocr_tick,
            "interval",
            seconds=settings.OCR_INTERVAL_SECONDS,
            id="ocr",
            replace_existing=True,
        )
        _scheduler.add_job(
            run_metrics_tick,
            "interval",
            seconds=settings.METRICS_INTERVAL_SECONDS,
            id="metrics",
            replace_existing=True,
        )
        logger.info("Background scheduler created with jobs: %s", _scheduler.get_jobs())
    return _scheduler


def start_scheduler() -> None:
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info(
            "Background scheduler started with jobs: %s",
            scheduler.get_jobs(),
        )


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Background scheduler stopped.")
