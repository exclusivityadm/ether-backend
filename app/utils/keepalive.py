# app/utils/keepalive.py

import asyncio
import logging
import os
import httpx

log = logging.getLogger("ether_v2.keepalive")


# ------------------------
# GET SELF URL AUTOMATICALLY
# ------------------------
def get_self_url():
    # Render provides HOST + PORT automatically
    host = os.getenv("RENDER_EXTERNAL_HOSTNAME")
    if host:
        return f"https://{host}/health"     # cloud URL
    return "http://127.0.0.1:10000/health"  # local fallback


# ------------------------
# PING API TO KEEP SERVICE AWAKE
# ------------------------
async def ping_self():
    url = get_self_url()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.get(url)
        log.info(f"[KeepAlive] SELF OK → {url}")
    except Exception as e:
        log.warning(f"[KeepAlive] SELF FAIL → {url} :: {e}")


# ------------------------
# VERIFY SUPABASE IS REACHABLE
# ------------------------
async def ping_supabase():
    url = os.getenv("SUPABASE_URL")
    if not url:
        log.warning("[KeepAlive] Missing SUPABASE_URL")
        return
    health = f"{url}/auth/v1/health"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.get(health)
        log.info("[KeepAlive] SUPABASE OK")
    except Exception as e:
        log.warning(f"[KeepAlive] SUPABASE FAIL :: {e}")


# ------------------------
# BACKGROUND TASK BOOTSTRAP
# ------------------------
def start_keepalive_tasks():
    async def self_loop():
        while True:
            await ping_self()
            await asyncio.sleep(60)    # 1 min

    async def supabase_loop():
        while True:
            await ping_supabase()
            await asyncio.sleep(300)   # 5 min

    loop = asyncio.get_event_loop()
    loop.create_task(self_loop())
    loop.create_task(supabase_loop())

    log.info("Keepalive services active ✓")
    return True
