# app/routers/controls.py
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Request

from app.schemas.controls import ControlActionResponse, ControlRecoveryRequest, ProjectControlRequest, ProviderControlRequest
from app.schemas.errors import EtherErrorResponse
from app.utils.audit import audit_event, audit_snapshot
from app.utils.control_plane import control_plane_state
from app.utils.phantom_core import phantom_core
from app.utils.phantom_keepalive import phantom_keepalive_lane
from app.utils.projects import get_project, list_projects
from app.utils.provider_readiness import provider_readiness_for_project, provider_readiness_for_suite
from app.utils.request_meta import extract_request_meta
from app.utils.sentinel import sentinel_engine
from app.utils.signal_verification_store import signal_verification_snapshot
from app.utils.webhook_store import webhook_snapshot

router = APIRouter(prefix="/controls", tags=["controls"])


OWNER_AUTH_SOURCES = {"admin", "owner", "phantom_core"}


def _actor(meta_source: Optional[str], details: Dict[str, Any]) -> str:
    return str(details.get("actor") or meta_source or "unknown").strip() or "unknown"


def _authority_context(meta_source: Optional[str], details: Dict[str, Any], extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    actor = _actor(meta_source, details)
    source_is_ownerish = actor.lower() in OWNER_AUTH_SOURCES or (meta_source or "").lower() in OWNER_AUTH_SOURCES
    context = {
        "authority_verified": bool(details.get("authority_verified") is True or source_is_ownerish),
        "owner_intent_recorded": bool(details.get("owner_intent_recorded") is True or source_is_ownerish),
        "reason_present": True,
        "actor_source": actor,
        "requested_details_keys": sorted((details or {}).keys()),
    }
    if extra:
        context.update(extra)
    return context


def _phantom_pause_response(gate: Dict[str, Any]):
    return EtherErrorResponse.forbidden(
        code="ETHER_PHANTOM_CORE_PAUSED_ACTION",
        message=gate.get("user_safe_message") or "This action is temporarily paused by Phantom Core.",
        details={
            "phantom_gate": gate,
            "recovery_required": gate.get("recovery_required", True),
            "operator_notes": [
                "This is not a crash or deletion. The action was contained before mutation.",
                "Review /phantom/status and /phantom/events before retrying.",
                "If appropriate, use /phantom/recovery or recorded owner authority context before retrying.",
            ],
        },
    )


def _gate_control_action(
    *,
    project_slug: str,
    action: str,
    actor: str,
    context: Dict[str, Any],
    provider: Optional[str] = None,
    incident_id: Optional[str] = None,
) -> Dict[str, Any]:
    return phantom_core.gate(
        project_slug=project_slug,
        action=action,
        actor=actor,
        severity="sovereignty_critical",
        resource_type="ether_control_plane",
        resource_id=provider or project_slug,
        provider=provider,
        context=context,
        incident_id=incident_id,
    )


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
    phantom = phantom_core.status()
    project_control = controls.get("projects", {}).get(project.slug, {})
    provider_controls = {
        key: value
        for key, value in controls.get("providers", {}).items()
        if value.get("project_slug") == project.slug
    }
    launch_blockers: list[str] = []
    if project_control.get("disabled"):
        launch_blockers.append(f"Project {project.slug} is disabled: {project_control.get('reason')}")
    for value in provider_controls.values():
        if value.get("disabled"):
            launch_blockers.append(f"Provider {value.get('provider')} is disabled: {value.get('reason')}")
    launch_blockers.extend(provider_readiness.get("launch_blockers") or [])
    if phantom.get("mode") in {"locked", "degraded", "safe_mode", "emergency_containment"}:
        launch_blockers.append(f"Phantom Core mode is {phantom.get('mode')}: dangerous writes are paused.")
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
        "phantom_core": phantom,
        "phantom_keepalive": phantom_keepalive_lane.status(),
        "signal_verification": signals,
        "webhooks": webhooks,
        "recent_control_events": control_events,
    }


def _recovery_notes(project_slug: str, provider: str | None = None) -> list[str]:
    notes = [
        "Review the original disable reason and linked incident before enabling.",
        "Check Phantom Core status, active containments, and recent allow/pause/deny events.",
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
        "phantom_core": phantom_core.status(),
        "phantom_keepalive": phantom_keepalive_lane.status(),
        "routes": {
            "summary": "/controls/summary",
            "blockers": "/controls/blockers",
            "history": "/controls/history",
            "impact": "/controls/impact/{project_slug}",
            "recover": "/controls/recover",
            "phantom_status": "/phantom/status",
            "phantom_events": "/phantom/events",
        },
    }


@router.get("/summary")
async def control_summary():
    controls = control_plane_state.snapshot()
    provider_readiness = provider_readiness_for_suite()
    signal = signal_verification_snapshot()
    audit = audit_snapshot(limit=20)
    phantom = phantom_core.status()
    keepalive = phantom_keepalive_lane.status()
    projects = [_project_control_impact(project.slug) for project in list_projects()]
    launch_blockers: dict[str, list[str]] = {}
    for row in projects:
        if row.get("launch_blocking"):
            launch_blockers[row.get("project_slug", "unknown")] = row.get("launch_blockers", [])
    phantom_blocking = phantom.get("mode") in {"locked", "degraded", "safe_mode", "emergency_containment"}
    return {
        "ok": True,
        "launch_blocking": bool(launch_blockers or controls.get("launch_blocking") or provider_readiness.get("launch_blockers") or phantom_blocking),
        "launch_blockers": launch_blockers,
        "controls": controls,
        "phantom_core": phantom,
        "phantom_keepalive": keepalive,
        "provider_readiness": provider_readiness,
        "signal_verification": signal,
        "audit": audit,
        "projects": projects,
    }


@router.get("/blockers")
async def control_blockers():
    summary = await control_summary()
    phantom = summary.get("phantom_core", {})
    phantom_blockers = []
    if phantom.get("mode") in {"locked", "degraded", "safe_mode", "emergency_containment"}:
        phantom_blockers.append(f"Phantom Core mode is {phantom.get('mode')}: {phantom.get('mode_reason')}")
    return {
        "ok": True,
        "launch_blocking": summary.get("launch_blocking"),
        "launch_blockers": summary.get("launch_blockers"),
        "control_blockers": summary.get("controls", {}).get("project_blockers", []) + summary.get("controls", {}).get("provider_blockers", []),
        "phantom_blockers": phantom_blockers,
        "provider_blockers": summary.get("provider_readiness", {}).get("launch_blockers", {}),
        "operator_notes": [
            "Project/provider controls are always launch-blocking until intentionally recovered.",
            "Phantom Core containment pauses dangerous writes without shutting down safe observation/logging.",
            "Provider readiness blockers may require credentials, signatures, or provider rails to be wired.",
            "Use /controls/impact/{project_slug} to inspect one project before recovery.",
            "Use /controls/history and /phantom/events to review why an action was contained or paused.",
        ],
    }


@router.get("/history")
async def control_history(project_slug: str | None = None, provider: str | None = None, incident_id: str | None = None, limit: int = 100):
    events = control_plane_state.events(project_slug=project_slug, provider=provider, incident_id=incident_id, limit=limit)
    return {
        "ok": True,
        "count": len(events),
        "events": events,
        "phantom_events_route": "/phantom/events",
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
    phantom = impact.get("phantom_core", {})
    return {
        "ok": True,
        "project_slug": impact["project_slug"],
        "ready_to_recover": (
            not impact.get("sentinel", {}).get("quarantine_status_counts", {}).get("active")
            and not impact.get("sentinel", {}).get("threat_status_counts", {}).get("open")
            and phantom.get("mode") not in {"locked", "degraded", "safe_mode", "emergency_containment"}
        ),
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

    actor = _actor(meta.source, body.details)
    gate = _gate_control_action(
        project_slug=project.slug,
        action="controls.recover",
        actor=actor,
        incident_id=body.incident_id,
        context=_authority_context(meta.source, body.details, {"enable_project": body.enable_project, "providers": body.providers}),
    )
    if gate.get("decision") != "allow":
        return _phantom_pause_response(gate)

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
            details={"reason": body.reason, "details": body.details, "incident_id": body.incident_id, "phantom_gate": gate},
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
            details={"reason": body.reason, "details": body.details, "incident_id": body.incident_id, "phantom_gate": gate},
        )
        actions.append({"control_type": "provider", "project_slug": state.project_slug, "provider": state.provider, "status": "enabled"})

    return {
        "ok": True,
        "project_slug": project.slug,
        "phantom_gate": gate,
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

    actor = _actor(meta.source, body.details)
    gate = _gate_control_action(
        project_slug=project.slug,
        action="controls.project.disable",
        actor=actor,
        incident_id=body.incident_id,
        context=_authority_context(meta.source, body.details),
    )
    if gate.get("decision") != "allow":
        return _phantom_pause_response(gate)

    state = control_plane_state.disable_project(project.slug, body.reason, body.details, actor=meta.source, incident_id=body.incident_id)
    audit_event(
        action="controls.project.disable",
        project_slug=project.slug,
        actor=meta.source,
        result="disabled",
        details={"reason": body.reason, "details": body.details, "incident_id": body.incident_id, "phantom_gate": gate},
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

    actor = _actor(meta.source, body.details)
    gate = _gate_control_action(
        project_slug=project.slug,
        action="controls.project.enable",
        actor=actor,
        incident_id=body.incident_id,
        context=_authority_context(meta.source, body.details),
    )
    if gate.get("decision") != "allow":
        return _phantom_pause_response(gate)

    state = control_plane_state.enable_project(project.slug, body.reason, body.details, actor=meta.source, incident_id=body.incident_id)
    audit_event(
        action="controls.project.enable",
        project_slug=project.slug,
        actor=meta.source,
        result="enabled",
        details={"reason": body.reason, "details": body.details, "incident_id": body.incident_id, "phantom_gate": gate},
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

    actor = _actor(meta.source, body.details)
    provider = body.provider.strip().lower()
    gate = _gate_control_action(
        project_slug=project.slug,
        action="controls.provider.disable",
        actor=actor,
        provider=provider,
        incident_id=body.incident_id,
        context=_authority_context(meta.source, body.details),
    )
    if gate.get("decision") != "allow":
        return _phantom_pause_response(gate)

    state = control_plane_state.disable_provider(project.slug, provider, body.reason, body.details, actor=meta.source, incident_id=body.incident_id)
    audit_event(
        action="controls.provider.disable",
        project_slug=project.slug,
        actor=meta.source,
        provider=state.provider,
        result="disabled",
        details={"reason": body.reason, "details": body.details, "incident_id": body.incident_id, "phantom_gate": gate},
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

    actor = _actor(meta.source, body.details)
    provider = body.provider.strip().lower()
    gate = _gate_control_action(
        project_slug=project.slug,
        action="controls.provider.enable",
        actor=actor,
        provider=provider,
        incident_id=body.incident_id,
        context=_authority_context(meta.source, body.details),
    )
    if gate.get("decision") != "allow":
        return _phantom_pause_response(gate)

    state = control_plane_state.enable_provider(project.slug, provider, body.reason, body.details, actor=meta.source, incident_id=body.incident_id)
    audit_event(
        action="controls.provider.enable",
        project_slug=project.slug,
        actor=meta.source,
        provider=state.provider,
        result="enabled",
        details={"reason": body.reason, "details": body.details, "incident_id": body.incident_id, "phantom_gate": gate},
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
