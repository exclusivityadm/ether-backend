# app/utils/keepalive.py
import anyio
import httpx
import os
import time

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

KEEPALIVE_INTERVAL_SECONDS = 300  # 5 minutes
REQUEST_TIMEOUT_SECONDS = 10
STALL_TIMEOUT_SECONDS = 20  # hard cap for any single ping attempt


def _now_str() -> str:
    return time.strftime("%X")


async def _ping_once(client: httpx.AsyncClient) -> None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("[KEEPALIVE] disabled — missing Supabase env vars")
        return

    url = f"{SUPABASE_URL}/rest/v1/rpc/keepalive_ping"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }

    # Hard cap so we never hang forever
    with anyio.move_on_after(STALL_TIMEOUT_SECONDS) as scope:
        resp = await client.post(url, headers=headers, json={})
        if scope.cancel_called:
            print(f"[KEEPALIVE] ping timed out (>{STALL_TIMEOUT_SECONDS}s) @ {_now_str()}")
            return

    print(f"[KEEPALIVE] ping ok ({resp.status_code}) @ {_now_str()}")


async def keepalive_worker() -> None:
    print("[KEEPALIVE] worker starting")

    # Use explicit timeouts to avoid any “hang forever” behavior
    timeout = httpx.Timeout(
        timeout=REQUEST_TIMEOUT_SECONDS,
        connect=REQUEST_TIMEOUT_SECONDS,
        read=REQUEST_TIMEOUT_SECONDS,
        write=REQUEST_TIMEOUT_SECONDS,
        pool=REQUEST_TIMEOUT_SECONDS,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        # deterministic schedule anchored to monotonic time
        next_run = anyio.current_time()

        while True:
            # schedule next run first so even errors don’t drift
            next_run += KEEPALIVE_INTERVAL_SECONDS

            try:
                await _ping_once(client)
            except Exception as e:
                print(f"[KEEPALIVE] ping error @ {_now_str()}: {e}")

            # Sleep until the next run; never sleep a single giant chunk.
            while True:
                now = anyio.current_time()
                remaining = next_run - now
                if remaining <= 0:
                    break
                await anyio.sleep(min(30, remaining))


async def keepalive_supervisor() -> None:
    """
    Ensures the worker cannot silently die.
    If it ever exits (for any reason), we restart it after a short backoff.
    """
    print("[KEEPALIVE] supervisor starting")
    while True:
        try:
            await keepalive_worker()
        except Exception as e:
            print(f"[KEEPALIVE] worker crashed @ {_now_str()}: {e}")
        # backoff before restart to avoid tight loop
        await anyio.sleep(5)
