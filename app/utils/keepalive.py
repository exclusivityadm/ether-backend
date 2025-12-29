# app/utils/keepalive.py
import asyncio
import httpx
import os
import time

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

KEEPALIVE_INTERVAL_SECONDS = 300  # 5 minutes


async def keepalive_loop():
    print("[KEEPALIVE] loop starting")

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("[KEEPALIVE] disabled — missing Supabase env vars")
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
                print(f"[KEEPALIVE] ping sent @ {time.strftime('%X')}")
            except Exception as e:
                print(f"[KEEPALIVE] ping failed: {e}")

            await asyncio.sleep(KEEPALIVE_INTERVAL_SECONDS)
