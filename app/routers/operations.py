from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.utils.audit import audit_event, audit_snapshot, list_recent_audit_events
from app.utils.project_supabase_signal import build_signal_payload, project_signal_readiness, record_and_verify_project_signal
from app.utils.projects import get_project, list_projects
from app.utils.request_meta import extract_request_meta
from app.utils.signal_lane import signal_lane_registry
from app.utils.signal_verification_store import list_signal_runs, signal_verification_snapshot

router = APIRouter(prefix="/operations", tags=["operations"])


CORE_SIGNAL_PROJECTS = ["circa_haus", "exclusivity"]


class ProjectSignalOperationRequest(BaseModel):
    signal_kind: str = "manual"
    status: str = "ok"
    lane_id: Optional[str] = None
    app_id: Optional[str] = None
    instance_id: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class MultiProjectSignalOperationRequest(ProjectSignalOperationRequest):
    project_slugs: List[str] = Field(default_factory=lambda: list(CORE_SIGNAL_PROJECTS))
    include_unconfigured: bool = True


class SuiteSmokeTestRequest(BaseModel):
    project_slugs: List[str] = Field(default_factory=lambda: list(CORE_SIGNAL_PROJECTS))
    include_unconfigured: bool = True
    signal_kind: str = "suite_smoke_test"
    status: str = "ok"
    meta: Dict[str, Any] = Field(default_factory=dict)


class CronSignalRequest(BaseModel):
    project_slugs: List[str] = Field(default_factory=lambda: list(CORE_SIGNAL_PROJECTS))
    signal_kind: str = "cron_keepalive"
    status: str = "ok"
    include_unconfigured: bool = False
    meta: Dict[str, Any] = Field(default_factory=dict)


def _project_status_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    projects = list_projects()
    rows: list[dict[str, Any]] = []
    ready_count = 0
    configured_count = 0
    active_lane_count = 0
    core_ready_count = 0

    verification = signal_verification_snapshot()
    last_success = verification.get("last_success_by_project", {})
    last_failure = verification.get("last_failure_by_project", {})

    for project in projects:
        readiness = project_signal_readiness(project.slug).to_dict()
        lanes = signal_lane_registry.list_lanes(project_slug=project.slug, limit=10)
        enabled_providers = sorted([name for name, enabled in project.provider_set.items() if enabled])
        ready_for_real_signal = bool(readiness.get("ready_for_real_signal"))
        fully_configured = (
            bool(readiness.get("supabase_url_configured"))
            and bool(readiness.get("service_role_configured"))
            and bool(readiness.get("signal_secret_configured"))
        )
        ready_count += 1 if ready_for_real_signal else 0
        configured_count += 1 if fully_configured else 0
        active_lane_count += len(lanes)
        if project.slug in CORE_SIGNAL_PROJECTS and ready_for_real_signal:
            core_ready_count += 1
        rows.append(
            {
                "slug": project.slug,
                "display_name": project.display_name,
                "status": project.status,
                "enabled_providers": enabled_providers,
                "feature_flags": project.feature_flags,
                "signal_readiness": readiness,
                "signal_verification": {
                    "last_success": last_success.get(project.slug),
                    "last_failure": last_failure.get(project.slug),
                },
                "recent_lanes": lanes,
                "recent_lane_count": len(lanes),
            }
        )

    summary = {
        "project_count": len(projects),
        "ready_for_real_signal_count": ready_count,
        "fully_configured_signal_secret_count": configured_count,
        "recent_lane_count": active_lane_count,
        "core_projects_expected": list(CORE_SIGNAL_PROJECTS),
        "core_ready_for_real_signal_count": core_ready_count,
        "core_ready_for_cron": core_ready_count == len(CORE_SIGNAL_PROJECTS),
        "core_last_verified_count": sum(1 for slug in CORE_SIGNAL_PROJECTS if last_success.get(slug)),
    }
    return rows, summary


@router.get("/suite/status")
async def suite_operations_status():
    rows, summary = _project_status_rows()
    suite_ready = summary["core_ready_for_cron"]
    return {
        "ok": True,
        "suite_ready_for_core_signal": suite_ready,
        "summary": summary,
        "signal_verification": signal_verification_snapshot(),
        "audit": audit_snapshot(limit=12),
        "cron": {
            "ready": suite_ready,
            "status_route": "/operations/cron/status",
            "signal_route": "/operations/cron/signal",
            "expected_projects": list(CORE_SIGNAL_PROJECTS),
        },
        "next_actions": [
            "Set project Supabase URL and service role variables in Render for Circa Haus and Exclusivity.",
            "Apply supabase/ether_signal_support.sql inside each connected Supabase project.",
            "Set per-project Ether signal secrets before requiring proof mode.",
            "Run POST /operations/suite/smoke for a bundled readiness + signal + audit smoke test.",
            "Run POST /operations/cron/signal when cron env and Supabase support are ready.",
            "Confirm verified signal runs appear in /operations/signal/history.",
        ],
        "projects": rows,
    }


@router.get("/cron/status")
async def cron_status():
    rows, summary = _project_status_rows()
    verification = signal_verification_snapshot()
    last_success = verification.get("last_success_by_project", {})
    ready_projects = [row["slug"] for row in rows if row["slug"] in CORE_SIGNAL_PROJECTS and row["signal_readiness"].get("ready_for_real_signal")]
    verified_projects = [slug for slug in CORE_SIGNAL_PROJECTS if last_success.get(slug)]
    missing_projects = [slug for slug in CORE_SIGNAL_PROJECTS if slug not in ready_projects]
    unverified_projects = [slug for slug in CORE_SIGNAL_PROJECTS if slug not in verified_projects]
    return {
        "ok": True,
        "cron_ready": summary["core_ready_for_cron"],
        "cron_verified": summary["core_last_verified_count"] == len(CORE_SIGNAL_PROJECTS),
        "expected_projects": list(CORE_SIGNAL_PROJECTS),
        "ready_projects": ready_projects,
        "verified_projects": verified_projects,
        "missing_projects": missing_projects,
        "unverified_projects": unverified_projects,
        "summary": summary,
        "signal_verification": verification,
        "routes": {
            "cron_signal": "/operations/cron/signal",
            "suite_smoke": "/operations/suite/smoke",
            "suite_status": "/operations/suite/status",
            "signal_history": "/operations/signal/history",
            "signal_health": "/operations/signal/health",
            "audit_summary": "/operations/audit/summary",
        },
        "operator_notes": [
            "Cron should only be considered ready when Circa Haus and Exclusivity are configured for real signal writes.",
            "Cron should only be considered verified when both projects have a successful write + readback signal run.",
            "If missing_projects is not empty, wire project Supabase env vars and apply the Supabase signal SQL first.",
            "If unverified_projects is not empty after wiring, run /operations/cron/signal and inspect failure reasons.",
        ],
    }


@router.post("/cron/signal")
async def cron_signal(body: CronSignalRequest, request: Request):
    meta = extract_request_meta(request)
    signal_body = MultiProjectSignalOperationRequest(
        project_slugs=body.project_slugs,
        include_unconfigured=body.include_unconfigured,
        signal_kind=body.signal_kind,
        status=body.status,
        instance_id="render-cron-or-admin-cron",
        meta={
            "cron_signal": True,
            "requested_by": meta.source,
            **body.meta,
        },
    )
    result = _trigger_many(signal_body, meta.source or "cron")
    audit_event(
        action="operations.cron_signal",
        actor=meta.source or "cron",
        result="ok" if result.get("ok") else "partial-or-failed",
        details={
            "ok_count": result.get("ok_count"),
            "total": result.get("total"),
            "projects": body.project_slugs,
        },
    )
    return {
        "ok": bool(result.get("ok")),
        "cron_ready_after_run": bool(result.get("ok")),
        "signal": result,
        "signal_verification": signal_verification_snapshot(),
        "audit": audit_snapshot(limit=12),
        "operator_notes": [
            "If ok is true, write + readback verification succeeded for every requested project.",
            "If ok is false, check readiness, Render env vars, Supabase SQL, service-role permissions, and readback failure reasons.",
        ],
    }


@router.get("/audit/recent")
async def recent_audit_events(
    limit: int = 50,
    project_slug: Optional[str] = None,
    action: Optional[str] = None,
    result: Optional[str] = None,
):
    events = list_recent_audit_events(limit=limit, project_slug=project_slug, action=action, result=result)
    return {
        "ok": True,
        "count": len(events),
        "events": events,
        "note": "Persistent audit events are used when available, with in-memory fallback.",
    }


@router.get("/audit/summary")
async def audit_summary(limit: int = 50):
    return {
        "ok": True,
        "audit": audit_snapshot(limit=limit),
    }


@router.get("/signal/health")
async def signal_health(project_slug: Optional[str] = None):
    snapshot = signal_verification_snapshot(project_slug=project_slug)
    last_success = snapshot.get("last_success_by_project", {})
    last_failure = snapshot.get("last_failure_by_project", {})
    launch_blockers: list[str] = []
    if project_slug:
        slug = project_slug.strip().lower()
        if not last_success.get(slug):
            launch_blockers.append(f"No verified signal run exists for {slug}.")
        if last_failure.get(slug) and not last_success.get(slug):
            launch_blockers.append(f"Latest available signal state for {slug} includes failure: {last_failure[slug].get('error')}")
    else:
        for slug in CORE_SIGNAL_PROJECTS:
            if not last_success.get(slug):
                launch_blockers.append(f"No verified signal run exists for core project {slug}.")
    return {
        "ok": True,
        "launch_blocking": bool(launch_blockers),
        "launch_blockers": launch_blockers,
        "snapshot": snapshot,
    }


@router.get("/signal/history")
async def signal_history(project_slug: Optional[str] = None, verified_ok: Optional[bool] = None, limit: int = 50):
    runs = list_signal_runs(project_slug=project_slug, verified_ok=verified_ok, limit=limit)
    return {
        "ok": True,
        "count": len(runs),
        "runs": runs,
    }


@router.get("/signal/readiness")
async def signal_readiness_index():
    return {
        "ok": True,
        "routes": {
            "suite_status": "/operations/suite/status",
            "suite_smoke_test": "/operations/suite/smoke",
            "cron_status": "/operations/cron/status",
            "cron_signal": "/operations/cron/signal",
            "signal_health": "/operations/signal/health",
            "signal_history": "/operations/signal/history",
            "audit_recent": "/operations/audit/recent",
            "audit_summary": "/operations/audit/summary",
            "all_project_readiness": "/readiness",
            "project_readiness": "/readiness/{project_slug}",
            "manual_project_signal": "/operations/signal/{project_slug}",
            "manual_multi_project_signal": "/operations/signal/all",
        },
        "intended_use": "Internal-only readiness, verified signal history, audit visibility, manual signal operations, Render Cron, admin smoke tests, and wiring-day verification.",
    }


def _trigger_for_project(project_slug: str, body: ProjectSignalOperationRequest, actor: Optional[str]) -> Dict[str, Any]:
    project = get_project(project_slug)
    if project is None:
        audit_event(
            action="operations.project_signal",
            project_slug=project_slug,
            actor=actor,
            result="project-not-found",
            details={"requested_project_slug": project_slug},
        )
        return {
            "ok": False,
            "project_slug": project_slug,
            "error": {
                "code": "ETHER_PROJECT_NOT_FOUND",
                "message": "Project could not be resolved for operations signal.",
                "project_slug": project_slug,
            },
        }

    readiness = project_signal_readiness(project.slug).to_dict()
    payload = build_signal_payload(
        project_slug=project.slug,
        lane_id=body.lane_id or f"operations:{project.slug}",
        status=body.status,
        source=actor or "operations",
        app_id=body.app_id or project.slug,
        instance_id=body.instance_id or "manual-or-cron",
        heartbeat_count=0,
        verified=False,
        meta={
            "operation": body.signal_kind,
            "requested_by": actor,
            **body.meta,
        },
    )
    payload["signal_kind"] = body.signal_kind.strip() or "manual"

    result = record_and_verify_project_signal(project_slug=project.slug, payload=payload).to_dict()
    audit_event(
        action="operations.project_signal",
        project_slug=project.slug,
        actor=actor,
        result="verified" if result.get("ok") else "failed",
        details={
            "readiness": readiness,
            "project_signal": result,
            "signal_kind": payload.get("signal_kind"),
        },
    )

    return {
        "ok": bool(result.get("ok")),
        "project_slug": project.slug,
        "readiness": readiness,
        "project_signal": result,
        "payload_summary": {
            "signal_kind": payload.get("signal_kind"),
            "lane_id": payload.get("lane_id"),
            "status": payload.get("status"),
            "app_id": payload.get("app_id"),
            "instance_id": payload.get("instance_id"),
        },
    }


def _trigger_many(body: MultiProjectSignalOperationRequest, actor: Optional[str]) -> Dict[str, Any]:
    requested = [slug.strip().lower() for slug in body.project_slugs if slug.strip()]
    if not requested:
        requested = [project.slug for project in list_projects()]

    results = []
    for slug in requested:
        readiness = project_signal_readiness(slug).to_dict()
        if not body.include_unconfigured and not readiness.get("ready_for_real_signal"):
            results.append(
                {
                    "ok": False,
                    "project_slug": slug,
                    "skipped": True,
                    "reason": "Project signal configuration is incomplete.",
                    "readiness": readiness,
                }
            )
            continue
        results.append(_trigger_for_project(slug, body, actor))

    ok_count = sum(1 for item in results if item.get("ok"))
    audit_event(
        action="operations.project_signal_all",
        actor=actor,
        result="verified" if ok_count == len(results) and results else "partial-or-failed",
        details={
            "requested": requested,
            "ok_count": ok_count,
            "total": len(results),
        },
    )
    return {
        "ok": bool(results) and ok_count == len(results),
        "ok_count": ok_count,
        "total": len(results),
        "results": results,
    }


@router.post("/suite/smoke")
async def suite_smoke_test(body: SuiteSmokeTestRequest, request: Request):
    meta = extract_request_meta(request)
    before_rows, before_summary = _project_status_rows()
    signal_body = MultiProjectSignalOperationRequest(
        project_slugs=body.project_slugs,
        include_unconfigured=body.include_unconfigured,
        signal_kind=body.signal_kind,
        status=body.status,
        meta={
            "suite_smoke_test": True,
            **body.meta,
        },
    )
    signal_result = _trigger_many(signal_body, meta.source)
    after_rows, after_summary = _project_status_rows()
    audit = audit_snapshot(limit=25)
    ok = bool(signal_result.get("ok"))
    audit_event(
        action="operations.suite_smoke_test",
        actor=meta.source,
        result="verified" if ok else "partial-or-failed",
        details={
            "signal_ok": ok,
            "ok_count": signal_result.get("ok_count"),
            "total": signal_result.get("total"),
            "before_summary": before_summary,
            "after_summary": after_summary,
        },
    )
    return {
        "ok": ok,
        "before": {"summary": before_summary, "projects": before_rows},
        "signal": signal_result,
        "after": {"summary": after_summary, "projects": after_rows},
        "signal_verification": signal_verification_snapshot(),
        "audit": audit,
        "operator_notes": [
            "If signal.ok is false because projects are not configured, wire Render env vars and apply Supabase SQL first.",
            "If signal writes fail, inspect write_result in /operations/signal/history.",
            "If readback fails, inspect Supabase table/RPC permissions and ether_signals rows.",
        ],
    }


@router.post("/signal/all")
async def trigger_all_project_signals(body: MultiProjectSignalOperationRequest, request: Request):
    meta = extract_request_meta(request)
    return _trigger_many(body, meta.source)


@router.post("/signal/{project_slug}")
async def trigger_project_signal(project_slug: str, body: ProjectSignalOperationRequest, request: Request):
    meta = extract_request_meta(request)
    return _trigger_for_project(project_slug, body, meta.source)
