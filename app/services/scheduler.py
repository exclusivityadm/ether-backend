# app/scheduler.py

from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.services.keepalive import ping_all_keepalives

scheduler: Optional[AsyncIOScheduler] = None


def start_scheduler() -> None:
    """
    Start a single global AsyncIO scheduler instance
    and register the keepalive job.
    """
    global scheduler

    if scheduler is not None and scheduler.running:
        return

    scheduler = AsyncIOScheduler()

    # Run every 5 minutes by default
    scheduler.add_job(
        ping_all_keepalives,
        IntervalTrigger(minutes=5),
        id="keepalive-job",
        replace_existing=True,
    )

    scheduler.start()


def shutdown_scheduler() -> None:
    """
    Gracefully shut down the scheduler.
    """
    global scheduler

    if scheduler is not None and scheduler.running:
        scheduler.shutdown()
