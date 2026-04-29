# app/routers/sentinel.py
from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.errors import EtherErrorResponse
from app.schemas.sentinel import (
    QuarantineReleaseRequest,
    QuarantineRequest,
    QuarantineResponse,
    SentinelStatusResponse,
    ThreatEventRequest,
    ThreatEventResponse,
    ThreatManualReviewRequest,
    ThreatReviewRequest,
    ThreatReviewResponse,
)
from app.utils.admin_ai import admin_ai_reviewer
from app.utils.audit import audit_event
from app.utils.control_plane import control_plane_state
from app.utils.projects import resolve_project
from app.utils.request_meta import extract_request_meta
from app.utils.sentinel import QuarantineRecord, ThreatRecord, sentinel_engine

router = APIRouter(prefix="/sentinel", tags=["sentinel"])


def _threat_payload(record: ThreatRecord) -> dict:
    return {
        "id": record.id,
        "project_slug": record.project_slug,
        "event_type": record.event_type,
        "severity": record.severity,
        "risk_score": record.risk_score,
        "disposition": record.disposition,
        "quarantined": record.quarantined,
        "actor_id": record.actor_id,
        "source_ip": record.source_ip,
        "status": record.status,
        "details": record.details,
        "created_at": record.created_at,
        "reviewed_at": record.reviewed_at,
        "reviewer": record.reviewer,
        "review_notes": record.review_notes,
    }


def _quarantine_payload(record: QuarantineRecord) -> dict:
    return {
        "id": record.id,
        "project_slug": record.project_slug,
        "target_type": record.target_type,
        "target_id": record.target_id,
        "reason": record.reason,
        "status": record.status,
        "expires_at": record.expires_at,
        "details": record.details,
        "created_at": record.created_at,
        "released_at": record.released_at,
        "released_by": record.released_by,
        "release_reason": record.release_reason,
    }


def _sentinel_launch_blockers(project_slug: str | None = None) -> tuple[bool, list[str]]:
    snapshot = sentinel_engine.snapshot(project_slug=project_slug)
    blockers: list[str] = []
    open_threats = int(snapshot.get("threat_status_counts", {}).get("open", 0) or 0)
    active_quarantines = int(snapshot.get("quarantine_status_counts", {}).get("active", 0) or 0)
    quarantine_dispositions = int(snapshot.get("disposition_counts", {}).get("quarantine", 0) or 0)

    if open_threats > 0:
        blockers.append(f"{open_threats} open Sentinel threat(s) require review.")
    if active_quarantines > 0:
        blockers.append(f"{active_quarantines} active Sentinel quarantine(s) exist.")
    if quarantine_dispositions > 0:
        blockers.append(f"{quarantine_dispositions} quarantine-level incident(s) are recorded.")
    return bool(blockers), blockers


@router.get("/status", response_model=SentinelStatusResponse)
async def sentinel_status(project_slug: str | None = None):
    snapshot = sentinel_engine.snapshot(project_slug=project_slug)
    launch_blocking, blockers = _sentinel_launch_blockers(project_slug=project_slug)
    return SentinelStatusResponse(
        ok=True,
        project_slug=project_slug,
        snapshot=snapshot,
        launch_blocking=launch_blocking,
        launch_blockers=blockers,
    )


@router.post("/events", response_model=ThreatEventResponse)
async def record_threat_event(request: Request, body: ThreatEventRequest):
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
            message="Project could not be resolved for sentinel event.",
            details={
                "project_slug": body.project_slug or meta.project_slug,
                "app_id": body.app_id or meta.app_id,
                "domain": body.domain or host,
                "source": meta.source,
            },
        )

    record = sentinel_engine.record_threat(
        project_slug=project.slug,
        event_type=body.event_type,
        severity=body.severity,
        actor_id=body.actor_id,
        source_ip=body.source_ip,
        details=body.details,
    )

    if record.quarantined and body.details.get("auto_disable_project"):
        control_plane_state.disable_project(
            project.slug,
            reason=f"Auto-disabled after sentinel event: {body.event_type}",
            details={"risk_score": record.risk_score, "threat_id": record.id, **body.details},
        )
    provider_name = str(body.details.get("provider") or "").strip().lower()
    if record.quarantined and provider_name and body.details.get("auto_disable_provider"):
        control_plane_state.disable_provider(
            project.slug,
            provider_name,
            reason=f"Auto-disabled after sentinel event: {body.event_type}",
            details={"risk_score": record.risk_score, "threat_id": record.id, **body.details},
        )

    audit_event(
        action="sentinel.event",
        project_slug=project.slug,
        actor=meta.source,
        result=record.disposition,
        details={
            "threat_id": record.id,
            "event_type": record.event_type,
            "severity": record.severity,
            "risk_score": record.risk_score,
            "quarantined": record.quarantined,
            "provider_auto_disabled": bool(record.quarantined and provider_name and body.details.get("auto_disable_provider")),
            "project_auto_disabled": bool(record.quarantined and body.details.get("auto_disable_project")),
        },
    )
    return ThreatEventResponse(
        ok=True,
        project_slug=record.project_slug,
        event_type=record.event_type,
        severity=record.severity,
        risk_score=record.risk_score,
        disposition=record.disposition,
        quarantined=record.quarantined,
        threat_id=record.id,
    )


@router.get("/events")
async def list_threat_events(project_slug: str | None = None, status: str | None = None, limit: int = 25):
    records = sentinel_engine.list_threats(project_slug=project_slug, status=status, limit=limit)
    return {
        "ok": True,
        "count": len(records),
        "threats": [_threat_payload(record) for record in records],
    }


@router.post("/review", response_model=ThreatReviewResponse)
async def review_threats(body: ThreatReviewRequest):
    threats = sentinel_engine.list_threats(project_slug=body.project_slug, limit=body.recent_limit)
    quarantines = sentinel_engine.list_quarantines(project_slug=body.project_slug)
    review = admin_ai_reviewer.review(
        project_slug=body.project_slug,
        threats=threats,
        quarantines=quarantines,
    )
    return ThreatReviewResponse(
        ok=True,
        project_slug=body.project_slug,
        ai_mode=str(review["ai_mode"]),
        summary=str(review["summary"]),
        recommended_actions=list(review["recommended_actions"]),
        counts=dict(review["counts"]),
    )


@router.post("/review/manual")
async def manual_review_threat(request: Request, body: ThreatManualReviewRequest):
    meta = extract_request_meta(request)
    record = sentinel_engine.review_threat(
        threat_id=body.threat_id,
        reviewer=meta.source,
        status=body.status,
        review_notes=body.review_notes,
    )
    if record is None:
        return EtherErrorResponse.not_found(
            code="ETHER_SENTINEL_THREAT_NOT_FOUND",
            message="Threat could not be found for review.",
            details={"threat_id": body.threat_id},
        )
    audit_event(
        action="sentinel.threat.review_manual",
        project_slug=record.project_slug,
        actor=meta.source,
        result=record.status,
        details={"threat_id": record.id, "review_notes": record.review_notes},
    )
    return {"ok": True, "threat": _threat_payload(record)}


@router.post("/quarantine", response_model=QuarantineResponse)
async def quarantine_target(request: Request, body: QuarantineRequest):
    meta = extract_request_meta(request)
    project = resolve_project(project_slug=body.project_slug, source=meta.source)
    if project is None:
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for quarantine action.",
            details={"project_slug": body.project_slug},
        )

    record = sentinel_engine.add_quarantine(
        project_slug=project.slug,
        target_type=body.target_type,
        target_id=body.target_id,
        reason=body.reason,
        expires_at=body.expires_at,
        details=body.details,
    )
    audit_event(
        action="sentinel.quarantine",
        project_slug=project.slug,
        actor=meta.source,
        result=record.status,
        details={"quarantine_id": record.id, "target_type": record.target_type, "target_id": record.target_id, "reason": record.reason},
    )
    return QuarantineResponse(
        ok=True,
        project_slug=record.project_slug,
        target_type=record.target_type,
        target_id=record.target_id,
        status=record.status,
        reason=record.reason,
        quarantine_id=record.id,
    )


@router.post("/quarantine/release")
async def release_quarantine_route(request: Request, body: QuarantineReleaseRequest):
    meta = extract_request_meta(request)
    record = sentinel_engine.release_quarantine(
        quarantine_id=body.quarantine_id,
        released_by=meta.source,
        release_reason=body.reason,
    )
    if record is None:
        return EtherErrorResponse.not_found(
            code="ETHER_SENTINEL_QUARANTINE_NOT_FOUND",
            message="Quarantine could not be found for release.",
            details={"quarantine_id": body.quarantine_id},
        )
    audit_event(
        action="sentinel.quarantine.release",
        project_slug=record.project_slug,
        actor=meta.source,
        result=record.status,
        details={"quarantine_id": record.id, "target_type": record.target_type, "target_id": record.target_id, "reason": body.reason},
    )
    return {"ok": True, "quarantine": _quarantine_payload(record)}


@router.get("/quarantines")
async def list_quarantines(project_slug: str | None = None, status: str | None = None, limit: int = 100):
    records = sentinel_engine.list_quarantines(project_slug=project_slug, status=status, limit=limit)
    return {
        "ok": True,
        "count": len(records),
        "quarantines": [_quarantine_payload(record) for record in records],
    }
