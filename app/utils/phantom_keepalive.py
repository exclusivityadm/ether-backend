from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from app.utils.audit import audit_event
from app.utils.project_supabase_signal import record_and_verify_project_signal
from app.utils.projects import get_project, list_projects

log = logging.getLogger("ether_v2.phantom_keepalive")

DEFAULT_PHANTOM_KEEPALIVE_SECONDS = 55 * 60


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PhantomKeepaliveLane:
    """
    Second-layer keepalive safety lane.

    This lane is owned by Phantom Core but uses Ether's existing project Supabase
    signal mechanism. It gives the suite a second meaningful signal source without
    replacing the ordinary app/Ether heartbeat path.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self.enabled = True
        self.interval_seconds = DEFAULT_PHANTOM_KEEPALIVE_SECONDS
        self.started = False
        self.run_count = 0
        self.last_started_at: Optional[str] = None
        self.last_completed_at: Optional[str] = None
        self.last_results: List[Dict[str, Any]] = []
        self.last_error: Optional[str] = None

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "ok": True,
                "name": "Phantom Core keepalive lane",
                "enabled": self.enabled,
                "started": self.started,
                "interval_seconds": self.interval_seconds,
                "run_count": self.run_count,
                "last_started_at": self.last_started_at,
                "last_completed_at": self.last_completed_at,
                "last_error": self.last_error,
                "last_results": list(self.last_results),
                "operator_notes": [
                    "This is a second safety lane and does not replace normal Ether signal lanes.",
                    "It writes meaningful Phantom health traffic through Ether's Supabase signal mechanism.",
                    "If a project is not configured for real Supabase signal writes, the result stays visible as not_configured instead of crashing Ether.",
                ],
            }

    def configure(self, *, enabled: Optional[bool] = None, interval_seconds: Optional[int] = None) -> Dict[str, Any]:
        with self._lock:
            if enabled is not None:
                self.enabled = bool(enabled)
            if interval_seconds is not None:
                self.interval_seconds = max(300, int(interval_seconds))
        audit_event(
            action="phantom.keepalive.configure",
            result="ok",
            details={"enabled": self.enabled, "interval_seconds": self.interval_seconds},
        )
        return self.status()

    async def start_background_loop(self) -> None:
        with self._lock:
            if self.started:
                return
            self.started = True
        audit_event(action="phantom.keepalive.start", result="ok", details={"interval_seconds": self.interval_seconds})
        while True:
            try:
                if self.enabled:
                    self.run_once(reason="scheduled")
            except Exception as exc:
                error = str(exc)[:240] or exc.__class__.__name__
                with self._lock:
                    self.last_error = error
                audit_event(action="phantom.keepalive.loop_error", result="failed", details={"error": error})
                log.warning("phantom_keepalive_loop_error=%s", error)
            await asyncio.sleep(self.interval_seconds)

    def run_once(self, *, reason: str = "manual", project_slug: Optional[str] = None) -> Dict[str, Any]:
        started_at = _utc_now_iso()
        projects = [get_project(project_slug)] if project_slug else list_projects()
        projects = [project for project in projects if project is not None]
        results: List[Dict[str, Any]] = []
        with self._lock:
            self.last_started_at = started_at
            self.run_count += 1

        for project in projects:
            lane_id = f"phantom-core:{project.slug}"
            payload = {
                "app_slug": project.slug,
                "signal_source": "phantom_core",
                "signal_kind": "phantom_keepalive",
                "lane_id": lane_id,
                "status": "phantom_alive",
                "app_id": "ether.phantom_core",
                "instance_id": "phantom-core-primary",
                "heartbeat_count": self.run_count,
                "verified": True,
                "received_at": _utc_now_iso(),
                "signal_payload": {
                    "reason": reason,
                    "phantom_lane": True,
                    "ether_mediated": True,
                    "project_display_name": project.display_name,
                },
            }
            verification = record_and_verify_project_signal(project_slug=project.slug, payload=payload).to_dict()
            results.append({
                "project_slug": project.slug,
                "ok": bool(verification.get("ok")),
                "verification": verification,
            })

        completed_at = _utc_now_iso()
        ok_count = sum(1 for row in results if row.get("ok"))
        with self._lock:
            self.last_completed_at = completed_at
            self.last_results = results
            self.last_error = None if ok_count == len(results) else "One or more Phantom keepalive writes failed or were not configured."

        audit_event(
            action="phantom.keepalive.run",
            result="verified" if results and ok_count == len(results) else "partial" if results else "no_projects",
            details={
                "reason": reason,
                "project_slug": project_slug,
                "project_count": len(results),
                "ok_count": ok_count,
                "started_at": started_at,
                "completed_at": completed_at,
                "results": results,
            },
        )
        return {
            "ok": bool(results and ok_count == len(results)),
            "reason": reason,
            "project_count": len(results),
            "ok_count": ok_count,
            "started_at": started_at,
            "completed_at": completed_at,
            "results": results,
        }


phantom_keepalive_lane = PhantomKeepaliveLane()
