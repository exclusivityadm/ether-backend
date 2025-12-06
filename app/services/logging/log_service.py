import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("ether")


def log_event(event: str, payload: Optional[Dict[str, Any]] = None) -> None:
    if payload is None:
        payload = {}
    logger.info("event=%s payload=%s", event, payload)
