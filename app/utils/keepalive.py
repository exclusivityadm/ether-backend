# app/utils/keepalive.py
import asyncio
import httpx
import os
import time

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

KEEPALIVE_INTERVAL_SECONDS = 300  # 5 minutes


async def keepalive_loop():
    print("[KEEPALIVE] supervisor loop starting")

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("[KEEPALIVE] disabled — missing Supabase env vars")
        return

    url = f"{SUPABASE_URL}/rest/v1/rpc/keepalive_ping"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            try:
                print("[KEEPALIVE] sending ping")
                await client.post(url, headers=headers)
                print(f"[KEEPALIVE] ping sent @ {time.strftime('%X')}")

                # Sleep in smaller chunks so cancellation is observable
                remaining = KEEPALIVE_INTERVAL_SECONDS
                while remaining > 0:
                    await asyncio.sleep(min(30, remaining))
                    remaining -= 30

            except asyncio.CancelledError:
                # This SHOULD NOT kill the loop
                print("[KEEPALIVE] cancellation intercepted — continuing")
                continue

            except Exception as e:
                print(f"[KEEPALIVE] error: {e}")
                await asyncio.sleep(30)
