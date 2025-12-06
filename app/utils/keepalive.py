import asyncio
import logging
import os
from typing import Awaitable, Callable

import httpx

logger = logging.getLogger("ether_v2.keepalive")


async def _periodic_task(name: str, interval_seconds: int, func: Callable[[], Awaitable[None]]):
    logger.info("Starting periodic task '%s' (interval=%ss)", name, interval_seconds)
    while True:
        try:
            await func()
        except Exception as exc:
            logger.warning("Keepalive task '%s' encountered an error: %s", name, exc)
        await asyncio.sleep(interval_seconds)


async def _ping_url(url: str) -> None:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url)
        logger.debug("Keepalive ping to %s → %s", url, resp.status_code)
    except Exception as exc:
        logger.debug("Keepalive ping to %s failed: %s", url, exc)


def start_keepalive() -> None:
    loop = asyncio.get_event_loop()

    port = os.getenv("PORT", "10000")
    base_url = os.getenv("SELF_BASE_URL", f"http://127.0.0.1:{port}")
    health_url = base_url.rstrip("/") + "/health"
    loop.create_task(_periodic_task("self-health", 60, lambda: _ping_url(health_url)))

    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    if supabase_url:
        supabase_health = supabase_url.rstrip("/") + "/auth/v1/health"
        loop.create_task(
            _periodic_task("supabase-health", 300, lambda: _ping_url(supabase_health))
        )

    logger.info("Keepalive tasks scheduled (self: %s, supabase: %s)", health_url, bool(supabase_url))
