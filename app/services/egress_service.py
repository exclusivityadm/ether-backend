from typing import Dict, Any
from datetime import datetime, timezone


def emit_event_stub(event_id: str) -> Dict[str, Any]:
    """
    Egress stub for Ether.

    This intentionally does NOTHING today.
    It exists to formalize the concept of egress
    so routing never leaks directly to integrations.
    """

    return {
        "emitted": False,
        "event_id": event_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "note": "Egress stub — no downstream routing enabled"
    }
