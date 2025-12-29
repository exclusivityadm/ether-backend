import asyncio
import logging
import httpx
import os

logger = logging.getLogger("keepalive")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

KEEPALIVE_INTERVAL_SECONDS = 300  # 5 minutes


async def _keepalive_loop():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        logger.warning("Keepalive disabled: Supabase env vars missing")
        return

    url = f"{SUPABASE_URL}/rest/v1/rpc/keepalive_ping"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=5) as client:
        while True:
            try:
                await client.post(url, headers=headers)
                logger.info("Supabase keepalive ping sent")
            except Exception as e:
                logger.error(f"Supabase keepalive failed: {e}")

            await asyncio.sleep(KEEPALIVE_INTERVAL_SECONDS)


def start_keepalive_tasks():
    loop = asyncio.get_event_loop()
    loop.create_task(_keepalive_loop())
