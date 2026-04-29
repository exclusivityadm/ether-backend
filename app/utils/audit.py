from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from app.utils.audit_store import (
    init_audit_store,
    list_persistent_audit_events,
    persist_audit_event,
    persistent_audit_snapshot,
)

log = logging.getLogger("ether_v2.audit")

_MAX_RECENT_EVENTS = 300
_recent_events: deque[Dict[str, Any]] = deque(maxlen=_MAX_RECENT_EVENTS)
_recent_events_lock = Lock()


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
    with _recent_events_lock:
        _recent_events.appendleft(event)
    try:
        persist_audit_event(event)
    except Exception as exc:
        log.warning("ether_audit_persist_failed=%s", exc)
    log.info("ether_audit_event=%s", event)
    return event


def initialize_audit() -> None:
    try:
        init_audit_store()
        audit_event(
            action="audit.initialize",
            result="ok",
            details={"storage": "sqlite", "mode": "persistent-plus-memory"},
        )
    except Exception as exc:
        log.warning("ether_audit_initialize_failed=%s", exc)


def list_recent_audit_events(
    *,
    limit: int = 50,
    project_slug: Optional[str] = None,
    action: Optional[str] = None,
    result: Optional[str] = None,
    include_persistent: bool = True,
) -> List[Dict[str, Any]]:
    if include_persistent:
        try:
            return list_persistent_audit_events(limit=limit, project_slug=project_slug, action=action, result=result)
        except Exception as exc:
            log.warning("ether_audit_persistent_read_failed=%s", exc)

    safe_limit = max(1, min(limit, _MAX_RECENT_EVENTS))
    project_filter = (project_slug or "").strip().lower()
    action_filter = (action or "").strip().lower()
    result_filter = (result or "").strip().lower()

    with _recent_events_lock:
        events = list(_recent_events)

    filtered: List[Dict[str, Any]] = []
    for event in events:
        if project_filter and (event.get("project_slug") or "").strip().lower() != project_filter:
            continue
        if action_filter and (event.get("action") or "").strip().lower() != action_filter:
            continue
        if result_filter and (event.get("result") or "").strip().lower() != result_filter:
            continue
        filtered.append(event)
        if len(filtered) >= safe_limit:
            break
    return filtered


def audit_snapshot(limit: int = 25, include_persistent: bool = True) -> Dict[str, Any]:
    if include_persistent:
        try:
            snapshot = persistent_audit_snapshot(limit=limit)
            snapshot["fallback_memory_recent_count"] = len(_recent_events)
            snapshot["retention"] = "persistent sqlite audit store plus in-memory recent buffer; move to managed Postgres/Supabase audit table when production scale requires it"
            return snapshot
        except Exception as exc:
            log.warning("ether_audit_persistent_snapshot_failed=%s", exc)

    events = list_recent_audit_events(limit=limit, include_persistent=False)
    action_counts: Dict[str, int] = {}
    project_counts: Dict[str, int] = {}
    result_counts: Dict[str, int] = {}
    for event in events:
        action_key = event.get("action") or "unknown"
        project_key = event.get("project_slug") or "suite"
        result_key = event.get("result") or "unknown"
        action_counts[action_key] = action_counts.get(action_key, 0) + 1
        project_counts[project_key] = project_counts.get(project_key, 0) + 1
        result_counts[result_key] = result_counts.get(result_key, 0) + 1
    return {
        "retention": "in-memory fallback recent events only; persistent audit store was unavailable",
        "max_recent_events": _MAX_RECENT_EVENTS,
        "included_recent_events": len(events),
        "action_counts": action_counts,
        "project_counts": project_counts,
        "result_counts": result_counts,
        "recent_events": events,
    }
