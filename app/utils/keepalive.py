# app/utils/keepalive.py

import asyncio
import logging
import os
import httpx
from supabase import create_client

log = logging.getLogger("ether_v2.keepalive")


# ---------------------------------------------------------
# Internal Keepalive: self ping every 60s
# Supabase Keepalive: auth health ping every 300s
# ---------------------------------------------------------

async def ping_self():
    url = os.getenv("SELF_URL", "http://127.0.0.1:10000/health")
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            await client.get(url)
        log.info(f"[KeepAlive] Self OK → {url}")
    except Exception as e:
        log.error(f"[KeepAlive] Self FAILED → {url} :: {e}")


async def ping_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        log.warning("[KeepAlive] Supabase environment variables missing — skipping")
        return

    client = create_client(url, key)

    try:
        client.functions.invoke("config")   # minimal valid endpoint call
        log.info("[KeepAlive] Supabase OK")
    except Exception as e:
        log.error(f"[KeepAlive] Supabase FAILED :: {e}")


# ---------------------------------------------------------
# Task Scheduler
# ---------------------------------------------------------

def start_keepalive_tasks():
    """
    This runs ONLY on deployment, and schedules ongoing background pings.
    No manual triggers required.
    """
    async def scheduler():
        while True:
            await ping_self()               # every 1 min
            await asyncio.sleep(60)

    async def supabase_scheduler():
        while True:
            await ping_supabase()           # every 5 min
            await asyncio.sleep(300)

    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())
    loop.create_task(supabase_scheduler())

    log.info("Keepalive tasks scheduled ✓")
    return True
