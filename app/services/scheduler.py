from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.keepalive import start_keepalive_scheduler

scheduler: Optional[AsyncIOScheduler] = None

def start_scheduler():
    """
    Starts the global scheduler. This now delegates all job creation
    to start_keepalive_scheduler() inside keepalive.py.
    """
    global scheduler

    if scheduler is not None and scheduler.running:
        return

    # create scheduler by calling keepalive.py’s scheduler
    scheduler = start_keepalive_scheduler()

    if scheduler is None:
        print("Keepalive: no jobs configured; scheduler will not start.")
        return

    print("Keepalive: scheduler started with jobs.")

def shutdown_scheduler():
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
