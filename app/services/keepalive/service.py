import logging
from typing import List
import httpx

from app.core.config import get_settings

logger = logging.getLogger("ether.keepalive")


def _targets() -> List[str]:
    settings = get_settings()
    urls: List[str] = []
    for val in (settings.RENDER_HEALTH_URL, settings.VERCEL_HEALTH_URL, settings.SUPABASE_HEALTH_URL):
        if val:
            urls.append(val)
    return urls


def run_keepalive() -> None:
    urls = _targets()
    if not urls:
        logger.debug("No keepalive targets configured; skipping ping.")
        return

    logger.info("Running keepalive ping for %d targets", len(urls))
    for url in urls:
        try:
            resp = httpx.get(url, timeout=10.0)
            logger.info("Keepalive OK %s -> %s", url, resp.status_code)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Keepalive failed for %s: %s", url, exc)
