from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.errors import EtherErrorResponse
from app.schemas.signal import (
    SignalHandshakeRequest,
    SignalHandshakeResponse,
    SignalHeartbeatRequest,
    SignalHeartbeatResponse,
)
from app.utils.audit import audit_event
from app.utils.control_plane import control_plane_state
from app.utils.project_supabase_signal import build_signal_payload, record_project_signal
from app.utils.projects import resolve_project
from app.utils.request_meta import extract_request_meta
from app.utils.signal_lane import signal_lane_registry

router = APIRouter(prefix="/signal", tags=["signal"])


def _provider_controls(project_slug: str, providers: dict[str, bool]) -> dict[str, bool]:
    return {
        provider: control_plane_state.provider_disabled(project_slug, provider)
        for provider, enabled in providers.items()
        if enabled
    }


@router.post("/handshake", response_model=SignalHandshakeResponse)
async def signal_handshake(request: Request, body: SignalHandshakeRequest):
    meta = extract_request_meta(request)
    host = (request.headers.get("host") or "").strip() or None

    project = resolve_project(
        project_slug=body.project_slug or meta.project_slug,
        source=meta.source,
        app_domain=body.domain or host,
        app_id=body.app_id or meta.app_id,
        bundle_id=body.bundle_id,
    )
    if project is None:
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for signal handshake.",
            details={
                "project_slug": body.project_slug or meta.project_slug,
                "app_id": body.app_id or meta.app_id,
                "domain": body.domain or host,
                "bundle_id": body.bundle_id,
                "source": meta.source,
            },
        )

    if control_plane_state.project_disabled(project.slug):
        return EtherErrorResponse.forbidden(
            code="ETHER_PROJECT_DISABLED",
            message="Project is currently disabled by Ether control state.",
            details={"project_slug": project.slug},
        )

    record = signal_lane_registry.handshake(
        project_slug=project.slug,
        app_id=body.app_id or meta.app_id,
        instance_id=body.instance_id,
        domain=body.domain or host,
        lane_id=body.lane_id,
        signal_secret=project.signal_secret_value,
        client_nonce=body.client_nonce,
        presented_proof=body.presented_proof,
        requested_capabilities=body.requested_capabilities,
    )

    audit_event(
        action="signal.handshake",
        project_slug=project.slug,
        actor=meta.source,
        result="accepted" if record.accepted else "awaiting-proof",
        details={
            "lane_id": record.lane_id,
            "verification_mode": record.verification_mode,
            "proof_required": record.proof_required,
            "instance_id": record.instance_id,
        },
    )

    resolved_by = "project_slug" if (body.project_slug or meta.project_slug) else "app_id" if (body.app_id or meta.app_id) else "domain_or_source"
    return SignalHandshakeResponse(
        ok=True,
        project_slug=project.slug,
        resolved_by=resolved_by,
        lane_id=record.lane_id,
        accepted=record.accepted,
        verified=record.verified,
        verification_mode=record.verification_mode,
        proof_required=record.proof_required,
        signal_ready=project.signal_secret_configured,
        server_nonce=record.server_nonce,
        next_heartbeat_seconds=60,
        control_state={"project_disabled": False},
        provider_controls=_provider_controls(project.slug, project.provider_set),
        feature_flags=project.feature_flags,
    )


@router.post("/heartbeat", response_model=SignalHeartbeatResponse)
async def signal_heartbeat(request: Request, body: SignalHeartbeatRequest):
    meta = extract_request_meta(request)
    host = (request.headers.get("host") or "").strip() or None

    project = resolve_project(
        project_slug=body.project_slug or meta.project_slug,
        source=meta.source,
        app_domain=body.domain or host,
        app_id=body.app_id or meta.app_id,
    )
    if project is None:
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for signal heartbeat.",
            details={
                "project_slug": body.project_slug or meta.project_slug,
                "app_id": body.app_id or meta.app_id,
                "domain": body.domain or host,
                "source": meta.source,
            },
        )

    result = signal_lane_registry.heartbeat(
        project_slug=project.slug,
        lane_id=body.lane_id,
        app_id=body.app_id or meta.app_id,
        instance_id=body.instance_id,
        status=body.status,
        signal_secret=project.signal_secret_value,
        client_nonce=body.client_nonce,
        presented_proof=body.presented_proof,
        meta=body.meta,
    )
    if result is None:
        return EtherErrorResponse.bad_request(
            code="ETHER_SIGNAL_LANE_UNKNOWN",
            message="Signal lane could not be resolved for heartbeat.",
            details={"project_slug": project.slug, "lane_id": body.lane_id},
        )

    project_signal = {
        "attempted": False,
        "configured": False,
        "ok": False,
        "mode": "not_attempted",
    }

    if result.accepted:
        payload = build_signal_payload(
            project_slug=project.slug,
            lane_id=body.lane_id,
            status=body.status,
            source=meta.source,
            app_id=body.app_id or meta.app_id,
            instance_id=body.instance_id or result.record.instance_id,
            heartbeat_count=result.record.heartbeat_count,
            verified=result.verified,
            meta=body.meta,
        )
        project_signal = record_project_signal(project_slug=project.slug, payload=payload).to_dict()

    audit_event(
        action="signal.heartbeat",
        project_slug=project.slug,
        actor=meta.source,
        result="accepted" if result.accepted else "awaiting-proof",
        details={
            "lane_id": body.lane_id,
            "verification_mode": result.verification_mode,
            "status": body.status,
            "project_signal": project_signal,
        },
    )

    return SignalHeartbeatResponse(
        ok=True,
        project_slug=project.slug,
        lane_id=body.lane_id,
        accepted=result.accepted,
        verified=result.verified,
        verification_mode=result.verification_mode,
        proof_required=result.proof_required,
        keepalive_recorded=result.keepalive_recorded and bool(project_signal.get("ok")),
        server_nonce=result.record.server_nonce,
        next_heartbeat_seconds=60,
        control_state={"project_disabled": control_plane_state.project_disabled(project.slug)},
        provider_controls=_provider_controls(project.slug, project.provider_set),
        project_signal=project_signal,
    )


@router.get("/lanes")
async def list_signal_lanes(project_slug: str | None = None, limit: int = 50):
    lanes = signal_lane_registry.list_lanes(project_slug=project_slug, limit=limit)
    return {
        "ok": True,
        "count": len(lanes),
        "lanes": lanes,
    }
