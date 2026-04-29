# app/routers/controls.py
from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.controls import ControlActionResponse, ControlRecoveryRequest, ProjectControlRequest, ProviderControlRequest
from app.schemas.errors import EtherErrorResponse
from app.utils.audit import audit_event, audit_snapshot, list_recent_audit_events
from app.utils.control_plane import control_plane_state
from app.utils.projects import get_project, list_projects
from app.utils.provider_readiness import provider_readiness_for_project, provider_readiness_for_suite
from app.utils.request_meta import extract_request_meta
from app.utils.sentinel import sentinel_engine
from app.utils.signal_verification_store import signal_verification_snapshot
from app.utils.webhook_store import webhook_snapshot

router = APIRouter(prefix="/controls", tags=["controls"])


def _project_control_impact(project_slug: str) -> dict:
    project = get_project(project_slug)
    if project is None:
        return {
            "ok": False,
            "project_slug": project_slug,
            "error": "Project could not be resolved.",
        }
    provider_readiness = provider_readiness_for_project(project.slug)
    sentinel = sentinel_engine.snapshot(project_slug=project.slug)
    signals = signal_verification_snapshot(project_slug=project.slug)
    webhooks = webhook_snapshot(project_slug=project.slug)
    control_events = control_plane_state.events(project_slug=project.slug, limit=25)
    controls = control_plane_state.snapshot()
    project_control = controls.get("projects", {}).get(project.slug, {})
    provider_controls = {
        key: value
        for key, value in controls.get("providers", {}).items()
        if value.get("project_slug") == project.slug
    }
    launch_blockers: list[str] = []
    if project_control.get("disabled"):
        launch_blockers.append(f"Project {project.slug} is disabled: {project_control.get('reason')}")
    for key, value in provider_controls.items():
        if value.get("disabled"):
            launch_blockers.append(f"Provider {value.get('provider')} is disabled: {value.get('reason')}")
    launch_blockers.extend(provider_readiness.get("launch_blockers") or [])
    return {
        "ok": True,
        "project_slug": project.slug,
        "display_name": project.display_name,
        "launch_blocking": bool(launch_blockers),
        "launch_blockers": launch_blockers,
        "control_state": {
            "project": project_control,
            "providers": provider_controls,
        },
        "provider_readiness": provider_readiness,
        "sentinel": sentinel,
        "signal_verification": signals,
        "webhooks": webhooks,
        "recent_control_events": control_events,
    }


def _recovery_notes(project_slug: str, provider: str | None = None) -> list[str]:
    notes = [
        "Review the original disable reason and linked incident before enabling.",
        "Check Sentinel status for unresolved threats or active quarantines.",
        "Check provider readiness and webhook/signature readiness if a provider rail is involved.",
        "Run suite smoke tests after recovery.",
        "Verify audit/control history shows the recovery reason clearly.",
    ]
    if provider:
        notes.append(f"After enabling {provider}, verify /providers/{project_slug}/readiness and relevant webhook test events.")
    else:
        notes.append(f"After enabling {project_slug}, verify /operations/suite/status and /operations/signal/health.")
    return notes


@router.get("")
async def list_control_state():
    return {
        "ok": True,
        "controls": control_plane_state.snapshot(),
        "routes": {
            "summary": "/controls/summary",
            "blockers": "/controls/blockers",
            "history": "/controls/history",
            "impact": "/controls/impact/{project_slug}",
            "recover": "/controls/recover",
        },
    }


@router.get("/summary")
async def control_summary():
    controls = control_plane_state.snapshot()
    provider_readiness = provider_readiness_for_suite()
    signal = signal_verification_snapshot()
    audit = audit_snapshot(limit=20)
    projects = [_project_control_impact(project.slug) for project in list_projects()]
    launch_blockers: dict[str, list[str]] = {}
    for row in projects:
        if row.get("launch_blocking"):
            launch_blockers[row.get("project_slug", "unknown")] = row.get("launch_blockers", [])
    return {
        "ok": True,
        "launch_blocking": bool(launch_blockers or controls.get("launch_blocking") or provider_readiness.get("launch_blockers")),
        "launch_blockers": launch_blockers,
        "controls": controls,
        "provider_readiness": provider_readiness,
        "signal_verification": signal,
        "audit": audit,
        "projects": projects,
    }


@router.get("/blockers")
async def control_blockers():
    summary = await control_summary()
    return {
        "ok": True,
        "launch_blocking": summary.get("launch_blocking"),
        "launch_blockers": summary.get("launch_blockers"),
        "control_blockers": summary.get("controls", {}).get("project_blockers", []) + summary.get("controls", {}).get("provider_blockers", []),
        "provider_blockers": summary.get("provider_readiness", {}).get("launch_blockers", {}),
        "operator_notes": [
            "Project/provider controls are always launch-blocking until intentionally recovered.",
            "Provider readiness blockers may require credentials, signatures, or provider rails to be wired.",
            "Use /controls/impact/{project_slug} to inspect one project before recovery.",
            "Use /controls/history to review who/what disabled a rail and why.",
        ],
    }


@router.get("/history")
async def control_history(project_slug: str | None = None, provider: str | None = None, incident_id: str | None = None, limit: int = 100):
    events = control_plane_state.events(project_slug=project_slug, provider=provider, incident_id=incident_id, limit=limit)
    return {
        "ok": True,
        "count": len(events),
        "events": events,
    }


@router.get("/impact/{project_slug}")
async def control_impact(project_slug: str):
    impact = _project_control_impact(project_slug)
    if not impact.get("ok"):
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for control impact.",
            details={"project_slug": project_slug},
        )
    return impact


@router.get("/recovery/{project_slug}")
async def recovery_diagnostics(project_slug: str):
    impact = _project_control_impact(project_slug)
    if not impact.get("ok"):
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for recovery diagnostics.",
            details={"project_slug": project_slug},
        )
    return {
        "ok": True,
        "project_slug": impact["project_slug"],
        "ready_to_recover": not impact.get("sentinel", {}).get("quarantine_status_counts", {}).get("active") and not impact.get("sentinel", {}).get("threat_status_counts", {}).get("open"),
        "impact": impact,
        "recovery_notes": _recovery_notes(impact["project_slug"]),
    }


@router.post("/recover")
async def recover_controls(body: ControlRecoveryRequest, request: Request):
    meta = extract_request_meta(request)
    project = get_project(body.project_slug)
    if project is None:
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for recovery action.",
            details={"project_slug": body.project_slug},
        )

    actions = []
    if body.enable_project:
        state = control_plane_state.enable_project(
            project.slug,
            body.reason,
            body.details,
            actor=meta.source,
            incident_id=body.incident_id,
        )
        audit_event(
            action="controls.project.recover",
            project_slug=project.slug,
            actor=meta.source,
            result="enabled",
            details={"reason": body.reason, "details": body.details, "incident_id": body.incident_id},
        )
        actions.append({"control_type": "project", "project_slug": state.project_slug, "status": "enabled"})

    for provider in body.providers:
        state = control_plane_state.enable_provider(
            project.slug,
            provider,
            body.reason,
            body.details,
            actor=meta.source,
            incident_id=body.incident_id,
        )
        audit_event(
            action="controls.provider.recover",
            project_slug=project.slug,
            actor=meta.source,
            provider=state.provider,
            result="enabled",
            details={"reason": body.reason, "details": body.details, "incident_id": body.incident_id},
        )
        actions.append({"control_type": "provider", "project_slug": state.project_slug, "provider": state.provider, "status": "enabled"})

    return {
        "ok": True,
        "project_slug": project.slug,
        "actions": actions,
        "post_recovery_impact": _project_control_impact(project.slug),
        "recovery_notes": _recovery_notes(project.slug),
    }


@router.post("/project/disable", response_model=ControlActionResponse)
async def disable_project(body: ProjectControlRequest, request: Request):
    meta = extract_request_meta(request)
    project = get_project(body.project_slug)
    if project is None:
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for control action.",
            details={"project_slug": body.project_slug},
        )

    state = control_plane_state.disable_project(project.slug, body.reason, body.details, actor=meta.source, incident_id=body.incident_id)
    audit_event(
        action="controls.project.disable",
        project_slug=project.slug,
        actor=meta.source,
        result="disabled",
        details={"reason": body.reason, "details": body.details, "incident_id": body.incident_id},
    )
    return ControlActionResponse(
        ok=True,
        control_type="project",
        project_slug=state.project_slug,
        status="disabled",
        reason=state.reason or body.reason,
        incident_id=body.incident_id,
        recovery_required=True,
        recovery_notes=_recovery_notes(project.slug),
    )


@router.post("/project/enable", response_model=ControlActionResponse)
async def enable_project(body: ProjectControlRequest, request: Request):
    meta = extract_request_meta(request)
    project = get_project(body.project_slug)
    if project is None:
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for control action.",
            details={"project_slug": body.project_slug},
        )

    state = control_plane_state.enable_project(project.slug, body.reason, body.details, actor=meta.source, incident_id=body.incident_id)
    audit_event(
        action="controls.project.enable",
        project_slug=project.slug,
        actor=meta.source,
        result="enabled",
        details={"reason": body.reason, "details": body.details, "incident_id": body.incident_id},
    )
    return ControlActionResponse(
        ok=True,
        control_type="project",
        project_slug=state.project_slug,
        status="enabled",
        reason=state.reason or body.reason,
        incident_id=body.incident_id,
        recovery_required=False,
        recovery_notes=_recovery_notes(project.slug),
    )


@router.post("/provider/disable", response_model=ControlActionResponse)
async def disable_provider(body: ProviderControlRequest, request: Request):
    meta = extract_request_meta(request)
    project = get_project(body.project_slug)
    if project is None:
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for control action.",
            details={"project_slug": body.project_slug},
        )

    state = control_plane_state.disable_provider(project.slug, body.provider, body.reason, body.details, actor=meta.source, incident_id=body.incident_id)
    audit_event(
        action="controls.provider.disable",
        project_slug=project.slug,
        actor=meta.source,
        provider=state.provider,
        result="disabled",
        details={"reason": body.reason, "details": body.details, "incident_id": body.incident_id},
    )
    return ControlActionResponse(
        ok=True,
        control_type="provider",
        project_slug=state.project_slug,
        provider=state.provider,
        status="disabled",
        reason=state.reason or body.reason,
        incident_id=body.incident_id,
        recovery_required=True,
        recovery_notes=_recovery_notes(project.slug, state.provider),
    )


@router.post("/provider/enable", response_model=ControlActionResponse)
async def enable_provider(body: ProviderControlRequest, request: Request):
    meta = extract_request_meta(request)
    project = get_project(body.project_slug)
    if project is None:
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for control action.",
            details={"project_slug": body.project_slug},
        )

    state = control_plane_state.enable_provider(project.slug, body.provider, body.reason, body.details, actor=meta.source, incident_id=body.incident_id)
    audit_event(
        action="controls.provider.enable",
        project_slug=project.slug,
        actor=meta.source,
        provider=state.provider,
        result="enabled",
        details={"reason": body.reason, "details": body.details, "incident_id": body.incident_id},
    )
    return ControlActionResponse(
        ok=True,
        control_type="provider",
        project_slug=state.project_slug,
        provider=state.provider,
        status="enabled",
        reason=state.reason or body.reason,
        incident_id=body.incident_id,
        recovery_required=False,
        recovery_notes=_recovery_notes(project.slug, state.provider),
    )
