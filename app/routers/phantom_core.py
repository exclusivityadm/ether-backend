from __future__ import annotations

from fastapi import APIRouter

from app.schemas.phantom_core import PhantomContainmentRequest, PhantomGateRequest, PhantomGateResponse, PhantomRecoveryRequest
from app.utils.phantom_core import phantom_core
from app.utils.phantom_keepalive import phantom_keepalive_lane

router = APIRouter(prefix="/phantom", tags=["phantom-core"])


@router.get("/status")
async def phantom_status():
    status = phantom_core.status()
    status["keepalive"] = phantom_keepalive_lane.status()
    return status


@router.get("/health")
async def phantom_health():
    status = phantom_core.heartbeat()
    keepalive = phantom_keepalive_lane.status()
    return {
        "ok": True,
        "mode": status.get("mode"),
        "last_heartbeat": status.get("last_heartbeat"),
        "active_containment_count": status.get("active_containment_count"),
        "casual_disable_supported": False,
        "emergency_containment_supported": True,
        "keepalive": {
            "enabled": keepalive.get("enabled"),
            "started": keepalive.get("started"),
            "interval_seconds": keepalive.get("interval_seconds"),
            "run_count": keepalive.get("run_count"),
            "last_completed_at": keepalive.get("last_completed_at"),
            "last_error": keepalive.get("last_error"),
        },
    }


@router.post("/gate", response_model=PhantomGateResponse)
async def phantom_gate(body: PhantomGateRequest):
    return phantom_core.gate(
        project_slug=body.project_slug,
        action=body.action,
        actor=body.actor,
        severity=body.severity,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        provider=body.provider,
        context=body.context,
        incident_id=body.incident_id,
    )


@router.post("/containment")
async def activate_containment(body: PhantomContainmentRequest):
    return phantom_core.containment(
        reason=body.reason,
        actor=body.actor,
        scope=body.scope,
        project_slug=body.project_slug,
        provider=body.provider,
        action_family=body.action_family,
        details=body.details,
        incident_id=body.incident_id,
    )


@router.post("/recovery")
async def recover_containment(body: PhantomRecoveryRequest):
    return phantom_core.recover(
        reason=body.reason,
        actor=body.actor,
        scope=body.scope,
        project_slug=body.project_slug,
        provider=body.provider,
        action_family=body.action_family,
        details=body.details,
        incident_id=body.incident_id,
    )


@router.get("/events")
async def phantom_events(limit: int = 100):
    return {
        "ok": True,
        "events": phantom_core.events(limit=limit),
    }


@router.get("/invariants")
async def phantom_invariants():
    status = phantom_core.status()
    return {
        "ok": True,
        "policy_version": status.get("policy_version"),
        "owner_invariants": status.get("owner_invariants"),
        "registered_irreversible_actions": status.get("registered_irreversible_actions"),
    }


@router.get("/keepalive/status")
async def phantom_keepalive_status():
    return phantom_keepalive_lane.status()


@router.post("/keepalive/run")
async def phantom_keepalive_run(project_slug: str | None = None):
    return phantom_keepalive_lane.run_once(reason="manual", project_slug=project_slug)


@router.post("/keepalive/configure")
async def phantom_keepalive_configure(enabled: bool | None = None, interval_seconds: int | None = None):
    return phantom_keepalive_lane.configure(enabled=enabled, interval_seconds=interval_seconds)
