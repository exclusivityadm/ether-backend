import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.keepalive import run_keepalives


log = logging.getLogger("ether.scheduler")
scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> None:
    global scheduler  # noqa: PLW0603
    if scheduler is not None:
        log.info("Scheduler already running.")
        return

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(run_keepalives, "interval", minutes=5, id="keepalive")
    scheduler.start()
    log.info("Scheduler started with keepalive job.")


def shutdown_scheduler() -> None:
    global scheduler  # noqa: PLW0603
    if scheduler:
        scheduler.shutdown(wait=False)
        log.info("Scheduler stopped.")
        scheduler = None
