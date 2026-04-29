from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from supabase import create_client

log = logging.getLogger("ether_v2.project_supabase_signal")


@dataclass(frozen=True)
class ProjectSignalWriteResult:
    attempted: bool
    configured: bool
    ok: bool
    project_slug: str
    mode: str
    target: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _env_key(project_slug: str, suffix: str) -> str:
    return f"{project_slug.strip().upper()}_{suffix.strip().upper()}"


def _env(project_slug: str, suffix: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(_env_key(project_slug, suffix), default or "")
    if value is None:
        return None
    value = value.strip()
    return value or None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_error(exc: Exception) -> str:
    text = str(exc).strip()
    if not text:
        return exc.__class__.__name__
    return text[:240]


def build_signal_payload(
    *,
    project_slug: str,
    lane_id: str,
    status: str,
    source: Optional[str],
    app_id: Optional[str],
    instance_id: Optional[str],
    heartbeat_count: int,
    verified: bool,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "app_slug": project_slug,
        "signal_source": source or "ether",
        "signal_kind": "heartbeat",
        "lane_id": lane_id,
        "status": status,
        "app_id": app_id,
        "instance_id": instance_id,
        "heartbeat_count": heartbeat_count,
        "verified": verified,
        "received_at": _utc_now_iso(),
        "signal_payload": dict(meta or {}),
    }


def record_project_signal(
    *,
    project_slug: str,
    payload: Dict[str, Any],
) -> ProjectSignalWriteResult:
    """
    Best-effort real Supabase keepalive/signal write.

    This intentionally never raises into the request path. Ether should continue
    to return a useful heartbeat response while recording whether project-level
    Supabase signal activity succeeded.

    Environment variables by project slug:
      {PROJECT}_SUPABASE_URL
      {PROJECT}_SUPABASE_SERVICE_ROLE_KEY
      {PROJECT}_SIGNAL_RPC, default ether_signal
      {PROJECT}_SIGNAL_TABLE, default ether_signals

    Preferred mode:
      RPC first, so each Supabase project can own its own validation/storage.

    Fallback mode:
      Insert into a conventional ether_signals table when the RPC is not ready.
    """
    slug = project_slug.strip().lower()
    url = _env(slug, "SUPABASE_URL")
    key = _env(slug, "SUPABASE_SERVICE_ROLE_KEY")
    rpc_name = _env(slug, "SIGNAL_RPC", "ether_signal") or "ether_signal"
    table_name = _env(slug, "SIGNAL_TABLE", "ether_signals") or "ether_signals"

    if not url or not key:
        return ProjectSignalWriteResult(
            attempted=False,
            configured=False,
            ok=False,
            project_slug=slug,
            mode="not_configured",
            error="Project Supabase URL or service role key is not configured.",
        )

    try:
        client = create_client(url, key)
    except Exception as exc:
        return ProjectSignalWriteResult(
            attempted=True,
            configured=True,
            ok=False,
            project_slug=slug,
            mode="client_init",
            error=_safe_error(exc),
        )

    try:
        client.rpc(rpc_name, {"payload": payload}).execute()
        return ProjectSignalWriteResult(
            attempted=True,
            configured=True,
            ok=True,
            project_slug=slug,
            mode="rpc",
            target=rpc_name,
        )
    except Exception as rpc_exc:
        log.info("Project signal RPC failed for %s; falling back to table insert: %s", slug, _safe_error(rpc_exc))

    try:
        client.table(table_name).insert(payload).execute()
        return ProjectSignalWriteResult(
            attempted=True,
            configured=True,
            ok=True,
            project_slug=slug,
            mode="table",
            target=table_name,
        )
    except Exception as table_exc:
        return ProjectSignalWriteResult(
            attempted=True,
            configured=True,
            ok=False,
            project_slug=slug,
            mode="failed",
            target=f"{rpc_name} or {table_name}",
            error=_safe_error(table_exc),
        )
