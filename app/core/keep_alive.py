"""
Keep-alive heartbeat for Ether services.

This module is intentionally generic so it can be reused for:
- Render web services
- Supabase edge functions / REST entrypoints
- Any other HTTP endpoint that should receive periodic traffic
to prevent aggressive "auto-sleep" behaviour.

Usage
-----
1. Add one of these to your .env file:

   KEEPALIVE_URL=https://your-service.onrender.com/health

   or, for multiple URLs (comma-separated):

   KEEPALIVE_URLS=https://svc-a/health,https://svc-b/health

2. Run locally:

   uvicorn app.main:app --reload  # normal API
   python -m app.core.keep_alive  # background pinger (optional)

3. In production, you can either:
   - Run this as a sidecar process, or
   - Convert `ping_forever` into a scheduled job / worker.

This file is completely side-effect free unless executed as __main__.
"""

import logging
import os
import time
from typing import List

import httpx

logger = logging.getLogger("ether.keep_alive")


def _get_urls() -> List[str]:
    """
    Resolve keep-alive URLs from environment variables.

    Priority:
    1. KEEPALIVE_URLS (comma-separated list)
    2. KEEPALIVE_URL (single URL)
    """
    raw = os.getenv("KEEPALIVE_URLS") or os.getenv("KEEPALIVE_URL") or ""
    urls = [u.strip() for u in raw.split(",") if u.strip()]
    return urls


def ping_once(timeout: float = 10.0) -> None:
    """
    Perform a single round of pings to all configured URLs.

    This is separated from the infinite loop so it can be:
    - Called from tests
    - Used in a cron/scheduled-job style environment
    """
    urls = _get_urls()
    if not urls:
        logger.warning(
            "No KEEPALIVE_URLS or KEEPALIVE_URL configured; "
            "keep-alive ping skipped."
        )
        return

    for url in urls:
        try:
            resp = httpx.get(url, timeout=timeout)
            logger.info("Keep-alive ping %s -> %s", url, resp.status_code)
        except Exception as exc:  # noqa: BLE001
            logger.error("Error during keep-alive ping to %s: %r", url, exc)


def ping_forever(interval_seconds: int = 300, timeout: float = 10.0) -> None:
    """
    Simple, robust infinite loop that pings all configured URLs every
    `interval_seconds` seconds.

    This is intentionally minimal: no frameworks, no async event loops,
    just a straightforward background worker you can run alongside Ether.
    """
    urls = _get_urls()
    if not urls:
        logger.warning(
            "No KEEPALIVE_URLS or KEEPALIVE_URL configured; "
            "keep-alive loop will exit."
        )
        return

    logger.info(
        "Starting keep-alive loop for %d URL(s) with interval=%ss",
        len(urls),
        interval_seconds,
    )

    while True:
        ping_once(timeout=timeout)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    # Allow running via: python -m app.core.keep_alive
    ping_forever()
