# app/services/keepalive.py

import httpx
import logging
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

log = logging.getLogger("keepalive")

# ----------------------------------------------------------
# Load keepalive URLs from environment
# ----------------------------------------------------------
def load_urls(env_name: str):
    raw = os.getenv(env_name, "")
    if not raw:
        return []
    return [url.strip() for url in raw.split(",") if url.strip()]


SUPABASE_URLS = load_urls("SUPABASE_KEEPALIVE_URLS")
RENDER_URLS = load_urls("RENDER_KEEPALIVE_URLS")
VERCEL_URLS = load_urls("VERCEL_KEEPALIVE_URLS")

ALL_URL_GROUPS = {
    "supabase": SUPABASE_URLS,
    "render": RENDER_URLS,
    "vercel": VERCEL_URLS,
}


# ----------------------------------------------------------
# Ping helper
# ----------------------------------------------------------
async def ping_url(url: str):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            log.info(f"[KEEPALIVE] {url} → {response.status_code}")
    except Exception as e:
        log.error(f"[KEEPALIVE] ERROR pinging {url}: {e}")


# ----------------------------------------------------------
# Schedule keepalive tasks
# ----------------------------------------------------------
def start_keepalive_scheduler():
    scheduler = AsyncIOScheduler()

    urls_added = 0

    for group_name, url_list in ALL_URL_GROUPS.items():
        for url in url_list:
            urls_added += 1
            scheduler.add_job(
                ping_url,
                trigger=IntervalTrigger(minutes=5),
                args=[url],
                id=f"keepalive_{group_name}_{url.replace('https://', '').replace('/', '_')}",
                max_instances=1,
                coalesce=True,
            )
            log.info(f"[KEEPALIVE] Added job for {url}")

    if urls_added == 0:
        log.info("[KEEPALIVE] No URLs configured — scheduler will not start.")
        return None

    scheduler.start()
    log.info("[KEEPALIVE] Scheduler started.")
    return scheduler
