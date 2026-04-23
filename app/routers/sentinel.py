# app/routers/sentinel.py
from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.errors import EtherErrorResponse
from app.schemas.sentinel import (
    QuarantineRequest,
    QuarantineResponse,
    ThreatEventRequest,
    ThreatEventResponse,
)
from app.utils.audit import audit_event
from app.utils.projects import resolve_project
from app.utils.request_meta import extract_request_meta
from app.utils.sentinel import sentinel_engine

router = APIRouter(prefix="/sentinel", tags=["sentinel"])


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
    audit_event(
        action="sentinel.event",
        project_slug=project.slug,
        actor=meta.source,
        result=record.disposition,
        details={
            "event_type": record.event_type,
            "severity": record.severity,
            "risk_score": record.risk_score,
            "quarantined": record.quarantined,
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
    )


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
        details={"target_type": record.target_type, "target_id": record.target_id, "reason": record.reason},
    )
    return QuarantineResponse(
        ok=True,
        project_slug=record.project_slug,
        target_type=record.target_type,
        target_id=record.target_id,
        status=record.status,
        reason=record.reason,
    )


@router.get("/quarantines")
async def list_quarantines(project_slug: str | None = None):
    records = sentinel_engine.list_quarantines(project_slug=project_slug)
    return {
        "ok": True,
        "count": len(records),
        "quarantines": [
            {
                "project_slug": record.project_slug,
                "target_type": record.target_type,
                "target_id": record.target_id,
                "reason": record.reason,
                "status": record.status,
                "expires_at": record.expires_at,
                "details": record.details,
            }
            for record in records
        ],
    }
