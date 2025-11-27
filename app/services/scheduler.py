# app/services/scheduler.py

from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.keepalive import start_keepalive_scheduler

scheduler: Optional[AsyncIOScheduler] = None

def start_scheduler():
    global scheduler

    if scheduler is not None and scheduler.running:
        return

    scheduler = start_keepalive_scheduler()

    if scheduler is None:
        print("Keepalive: no jobs configured; scheduler will not start.")
        return

    print("Keepalive: scheduler started with jobs.")

def shutdown_scheduler():
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
