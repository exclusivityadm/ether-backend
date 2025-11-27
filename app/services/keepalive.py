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


SUPABASE_URLS = load_urls("SUPABASE_KEEPALIVE_URLS")
RENDER_URLS = load_urls("RENDER_KEEPALIVE_URLS")
VERCEL_URLS = load_urls("VERCEL_KEEPALIVE_URLS")

ALL_GROUPS = {
    "supabase": SUPABASE_URLS,
    "render": RENDER_URLS,
    "vercel": VERCEL_URLS,
}


async def ping_url(url: str):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
            log.info(f"[KEEPALIVE] {url} → {r.status_code}")
    except Exception as e:
        log.error(f"[KEEPALIVE] ERROR pinging {url}: {e}")


def start_keepalive_scheduler():
    scheduler = AsyncIOScheduler()
    jobs_added = 0

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

            log.info(f"[KEEPALIVE] Added job: {url}")
            jobs_added += 1

    if jobs_added == 0:
        return None

    scheduler.start()
    return scheduler
