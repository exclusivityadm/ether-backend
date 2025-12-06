import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.keepalive.keepalive import keepalive_tick
from app.services.logging.log_service import log_event

logger = logging.getLogger("ether.scheduler")


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(keepalive_tick, "interval", minutes=5, id="keepalive")
    # simple placeholders for OCR + metrics ticks
    scheduler.add_job(lambda: log_event("ocr_tick", {}), "interval", minutes=10, id="ocr")
    scheduler.add_job(
        lambda: log_event("metrics_tick", {}), "interval", minutes=15, id="metrics"
    )
    return scheduler
