import asyncio
import logging
from typing import List

import httpx

from app.core.config import get_settings


log = logging.getLogger("ether.keepalive")
settings = get_settings()


def _parse_urls(csv: str) -> List[str]:
    return [u.strip() for u in csv.split(",") if u.strip()]


async def _ping_url(client: httpx.AsyncClient, url: str) -> None:
    try:
        resp = await client.get(url, timeout=5)
        log.info("[KEEPALIVE] %s -> %s", url, resp.status_code)
    except Exception as exc:  # noqa: BLE001
        log.warning("[KEEPALIVE] Failed to reach %s: %s", url, exc)


async def run_keepalives() -> None:
    urls: List[str] = []
    urls.extend(_parse_urls(settings.SUPABASE_KEEPALIVE_URLS))
    urls.extend(_parse_urls(settings.RENDER_KEEPALIVE_URLS))
    urls.extend(_parse_urls(settings.VERCEL_KEEPALIVE_URLS))

    if not urls:
        log.info("[KEEPALIVE] No keepalive URLs configured.")
        return

    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[_ping_url(client, u) for u in urls])
