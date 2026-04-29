from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from supabase import create_client

from app.utils.signal_verification_store import save_signal_run

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


@dataclass(frozen=True)
class ProjectSignalReadbackResult:
    attempted: bool
    configured: bool
    ok: bool
    project_slug: str
    mode: str
    target: Optional[str] = None
    matched_id: Optional[str] = None
    matched_received_at: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectSignalVerificationResult:
    ok: bool
    project_slug: str
    signal_kind: str
    lane_id: Optional[str]
    write: Dict[str, Any]
    readback: Dict[str, Any]
    run: Dict[str, Any]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectSignalReadiness:
    project_slug: str
    supabase_url_configured: bool
    service_role_configured: bool
    signal_secret_configured: bool
    rpc_name: str
    table_name: str
    ready_for_real_signal: bool
    notes: list[str]

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


def project_signal_readiness(project_slug: str) -> ProjectSignalReadiness:
    slug = project_slug.strip().lower()
    url_configured = bool(_env(slug, "SUPABASE_URL"))
    service_role_configured = bool(_env(slug, "SUPABASE_SERVICE_ROLE_KEY"))
    signal_secret_configured = bool(_env(slug, "ETHER_SIGNAL_SECRET") or _env(slug, "SIGNAL_SECRET"))
    rpc_name = _env(slug, "SIGNAL_RPC", "ether_signal") or "ether_signal"
    table_name = _env(slug, "SIGNAL_TABLE", "ether_signals") or "ether_signals"
    notes: list[str] = []

    if not url_configured:
        notes.append(f"{_env_key(slug, 'SUPABASE_URL')} is missing.")
    if not service_role_configured:
        notes.append(f"{_env_key(slug, 'SUPABASE_SERVICE_ROLE_KEY')} is missing.")
    if not signal_secret_configured:
        notes.append(f"{_env_key(slug, 'ETHER_SIGNAL_SECRET')} is missing; proof mode can remain pending until configured.")
    if not notes:
        notes.append("Project signal lane has the required server-side configuration for real Supabase activity.")

    return ProjectSignalReadiness(
        project_slug=slug,
        supabase_url_configured=url_configured,
        service_role_configured=service_role_configured,
        signal_secret_configured=signal_secret_configured,
        rpc_name=rpc_name,
        table_name=table_name,
        ready_for_real_signal=url_configured and service_role_configured,
        notes=notes,
    )


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


def _client_for_project(project_slug: str):
    slug = project_slug.strip().lower()
    url = _env(slug, "SUPABASE_URL")
    key = _env(slug, "SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None, ProjectSignalWriteResult(
            attempted=False,
            configured=False,
            ok=False,
            project_slug=slug,
            mode="not_configured",
            error="Project Supabase URL or service role key is not configured.",
        )
    try:
        return create_client(url, key), None
    except Exception as exc:
        return None, ProjectSignalWriteResult(
            attempted=True,
            configured=True,
            ok=False,
            project_slug=slug,
            mode="client_init",
            error=_safe_error(exc),
        )


def record_project_signal(
    *,
    project_slug: str,
    payload: Dict[str, Any],
) -> ProjectSignalWriteResult:
    """
    Best-effort real Supabase keepalive/signal write.
    """
    slug = project_slug.strip().lower()
    rpc_name = _env(slug, "SIGNAL_RPC", "ether_signal") or "ether_signal"
    table_name = _env(slug, "SIGNAL_TABLE", "ether_signals") or "ether_signals"
    client, client_error = _client_for_project(slug)
    if client_error is not None:
        return client_error

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


def readback_project_signal(
    *,
    project_slug: str,
    payload: Dict[str, Any],
) -> ProjectSignalReadbackResult:
    slug = project_slug.strip().lower()
    table_name = _env(slug, "SIGNAL_TABLE", "ether_signals") or "ether_signals"
    client, client_error = _client_for_project(slug)
    if client_error is not None:
        return ProjectSignalReadbackResult(
            attempted=client_error.attempted,
            configured=client_error.configured,
            ok=False,
            project_slug=slug,
            mode=client_error.mode,
            target=client_error.target,
            error=client_error.error,
        )

    lane_id = payload.get("lane_id")
    received_at = payload.get("received_at")
    heartbeat_count = payload.get("heartbeat_count")
    app_slug = payload.get("app_slug") or slug

    try:
        query = (
            client.table(table_name)
            .select("id, app_slug, lane_id, heartbeat_count, received_at, signal_kind, status")
            .eq("app_slug", app_slug)
            .eq("lane_id", lane_id)
            .order("received_at", desc=True)
            .limit(5)
        )
        response = query.execute()
        rows = getattr(response, "data", None) or []
        for row in rows:
            if str(row.get("heartbeat_count")) == str(heartbeat_count) or str(row.get("received_at")) == str(received_at):
                return ProjectSignalReadbackResult(
                    attempted=True,
                    configured=True,
                    ok=True,
                    project_slug=slug,
                    mode="table_readback",
                    target=table_name,
                    matched_id=str(row.get("id")) if row.get("id") is not None else None,
                    matched_received_at=str(row.get("received_at")) if row.get("received_at") is not None else None,
                )
        return ProjectSignalReadbackResult(
            attempted=True,
            configured=True,
            ok=False,
            project_slug=slug,
            mode="table_readback_no_match",
            target=table_name,
            error="Signal write was not visible in readback query.",
        )
    except Exception as exc:
        return ProjectSignalReadbackResult(
            attempted=True,
            configured=True,
            ok=False,
            project_slug=slug,
            mode="table_readback_failed",
            target=table_name,
            error=_safe_error(exc),
        )


def record_and_verify_project_signal(
    *,
    project_slug: str,
    payload: Dict[str, Any],
) -> ProjectSignalVerificationResult:
    slug = project_slug.strip().lower()
    write = record_project_signal(project_slug=slug, payload=payload)
    readback = readback_project_signal(project_slug=slug, payload=payload) if write.ok else ProjectSignalReadbackResult(
        attempted=False,
        configured=write.configured,
        ok=False,
        project_slug=slug,
        mode="not_attempted_write_failed",
        error=write.error,
    )
    verified_ok = bool(write.ok and readback.ok)
    error = None if verified_ok else (readback.error or write.error or "Signal verification failed.")
    payload_summary = {
        "signal_kind": payload.get("signal_kind"),
        "lane_id": payload.get("lane_id"),
        "status": payload.get("status"),
        "app_id": payload.get("app_id"),
        "instance_id": payload.get("instance_id"),
        "heartbeat_count": payload.get("heartbeat_count"),
        "received_at": payload.get("received_at"),
    }
    run = save_signal_run(
        project_slug=slug,
        signal_kind=str(payload.get("signal_kind") or "unknown"),
        lane_id=str(payload.get("lane_id")) if payload.get("lane_id") is not None else None,
        status="verified" if verified_ok else "failed",
        write_ok=write.ok,
        readback_ok=readback.ok,
        verified_ok=verified_ok,
        write_mode=write.mode,
        write_target=write.target,
        readback_mode=readback.mode,
        readback_target=readback.target,
        error=error,
        write_result=write.to_dict(),
        readback_result=readback.to_dict(),
        payload_summary=payload_summary,
        recorded_at=_utc_now_iso(),
    )
    return ProjectSignalVerificationResult(
        ok=verified_ok,
        project_slug=slug,
        signal_kind=str(payload.get("signal_kind") or "unknown"),
        lane_id=str(payload.get("lane_id")) if payload.get("lane_id") is not None else None,
        write=write.to_dict(),
        readback=readback.to_dict(),
        run=run,
        error=error,
    )
