from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

log = logging.getLogger("ether_v2.audit")


def audit_event(
    action: str,
    project_slug: Optional[str] = None,
    actor: Optional[str] = None,
    provider: Optional[str] = None,
    result: str = "accepted",
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "project_slug": project_slug,
        "actor": actor,
        "provider": provider,
        "result": result,
        "details": details or {},
    }
    log.info("ether_audit_event=%s", event)
    return event
