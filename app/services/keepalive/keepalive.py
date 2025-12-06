import logging
from datetime import datetime

from app.services.logging.log_service import log_event

logger = logging.getLogger("ether.keepalive")


def keepalive_tick() -> None:
    now = datetime.utcnow().isoformat()
    log_event("keepalive_tick", {"timestamp": now})
    logger.debug("Keepalive heartbeat at %s", now)
