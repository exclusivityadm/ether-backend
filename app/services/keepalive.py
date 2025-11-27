# app/services/keepalive.py

import httpx
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

log = logging.getLogger("keepalive")


def load_urls(env_name: str):
    raw = os.getenv(env_name, "")
    if not raw:
        return []
    return [url.strip() for url in raw.split(",") if url.strip()]


async def ping_url(url: str):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
            log.info(f"[KEEPALIVE] {url} → {r.status_code}")
    except Exception as e:
        log.error(f"[KEEPALIVE] ERROR pinging {url}: {e}")


def start_keepalive_scheduler():
    """
    Load environment variables *here*, at runtime,
    so Render/.env variables actually exist.
    """
    scheduler = AsyncIOScheduler()
    jobs_added = 0

    # dynamically load URLs at call-time
    ALL_GROUPS = {
        "supabase": load_urls("SUPABASE_KEEPALIVE_URLS"),
        "render": load_urls("RENDER_KEEPALIVE_URLS"),
        "vercel": load_urls("VERCEL_KEEPALIVE_URLS"),
    }

    for group, urls in ALL_GROUPS.items():
        for url in urls:
            job_id = f"keepalive_{group}_{url.replace('https://','').replace('/', '_')}"

            scheduler.add_job(
                ping_url,
                trigger=IntervalTrigger(minutes=5),
                args=[url],
                id=job_id,
                replace_existing=True,
            )

            log.info(f"[KEEPALIVE] Added job for {group}: {url}")
            jobs_added += 1

    if jobs_added == 0:
        return None

    scheduler.start()
    return scheduler
