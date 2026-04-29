# app/routers/webhooks.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Request

from app.schemas.errors import EtherErrorResponse
from app.utils.audit import audit_event
from app.utils.control_plane import control_plane_state
from app.utils.projects import get_project, list_projects
from app.utils.provider_broker import provider_enabled
from app.utils.request_meta import extract_request_meta
from app.utils.webhook_signature import verify_webhook_signature
from app.utils.webhook_store import (
    canonical_payload_hash,
    event_exists,
    list_webhook_events,
    make_event_uid,
    save_webhook_event,
    webhook_snapshot,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalized_provider(provider: str) -> str:
    return (provider or "").strip().lower()


def _extract_provider_event_id(provider: str, payload: Dict[str, Any], request: Request) -> Optional[str]:
    normalized = _normalized_provider(provider)
    headers = request.headers

    if normalized == "stripe":
        value = payload.get("id") or headers.get("stripe-event-id")
        return str(value).strip() if value else None
    if normalized == "twilio":
        value = payload.get("MessageSid") or payload.get("SmsSid") or payload.get("CallSid")
        return str(value).strip() if value else None
    if normalized == "canva":
        value = payload.get("id") or payload.get("event_id") or payload.get("notification_id")
        return str(value).strip() if value else None
    if normalized == "apliiq":
        value = payload.get("id") or payload.get("event_id") or payload.get("order_id")
        return str(value).strip() if value else None
    if normalized == "printful":
        value = payload.get("id") or payload.get("event_id")
        if not value and isinstance(payload.get("data"), dict):
            value = payload.get("data", {}).get("id")
        return str(value).strip() if value else None

    value = payload.get("id") or payload.get("event_id") or payload.get("eventId")
    return str(value).strip() if value else None


def _extract_event_type(provider: str, payload: Dict[str, Any]) -> Optional[str]:
    normalized = _normalized_provider(provider)
    if normalized == "stripe":
        value = payload.get("type")
    elif normalized == "twilio":
        value = payload.get("MessageStatus") or payload.get("SmsStatus") or payload.get("CallStatus") or payload.get("event_type")
    elif normalized in {"canva", "apliiq", "printful"}:
        value = payload.get("type") or payload.get("event_type") or payload.get("event")
    else:
        value = payload.get("type") or payload.get("event_type") or payload.get("event")
    return str(value).strip() if value else None


def _safe_headers(provider: str, request: Request, signature: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "host": request.headers.get("host"),
        "user_agent": request.headers.get("user-agent"),
        "content_type": request.headers.get("content-type"),
        "signature_header_present": signature.get("header_present"),
        "expected_signature_header": signature.get("expected_header"),
        "signature_mode": signature.get("mode"),
    }


def _validation_result(
    *,
    project_slug: str,
    provider: str,
    payload: Dict[str, Any],
    request: Request,
    raw_body: bytes,
) -> Dict[str, Any]:
    normalized = _normalized_provider(provider)
    provider_event_id = _extract_provider_event_id(normalized, payload, request)
    event_type = _extract_event_type(normalized, payload)
    signature = verify_webhook_signature(
        project_slug=project_slug,
        provider=normalized,
        headers=dict(request.headers),
        raw_body=raw_body,
        payload=payload,
        request_url=str(request.url),
    ).to_dict()
    warnings: list[str] = []

    if not provider_event_id:
        warnings.append("Provider event id was not found; payload hash will be used for idempotency.")
    if not event_type:
        warnings.append("Provider event type was not found.")
    warnings.extend(signature.get("warnings") or [])

    if signature.get("configured") and not signature.get("verified"):
        warnings.append("Provider signature verification failed; this webhook should not be trusted.")
    elif not signature.get("configured"):
        warnings.append("Provider signature verification is not configured yet; event is accepted only as wiring-stage intake.")

    return {
        "provider": normalized,
        "provider_event_id": provider_event_id,
        "event_type": event_type,
        "signature": signature,
        "warnings": warnings,
        "signature_verified": bool(signature.get("verified")),
        "signature_configured": bool(signature.get("configured")),
        "verification_mode": signature.get("mode"),
    }


def _signature_should_reject(validation: Dict[str, Any]) -> bool:
    signature = validation.get("signature") or {}
    return bool(signature.get("configured") and not signature.get("verified"))


def _persist_webhook_attempt(
    *,
    project_slug: str,
    provider: str,
    request: Request,
    payload: Dict[str, Any],
    status: str,
    accepted: bool,
    duplicate: bool,
    validation: Dict[str, Any],
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    payload_hash = canonical_payload_hash(payload)
    provider_event_id = validation.get("provider_event_id")
    event_uid = make_event_uid(project_slug=project_slug, provider=provider, provider_event_id=provider_event_id, payload_hash=payload_hash)
    return save_webhook_event(
        event_uid=event_uid,
        project_slug=project_slug,
        provider=provider,
        event_type=validation.get("event_type"),
        provider_event_id=provider_event_id,
        status=status,
        accepted=accepted,
        duplicate=duplicate,
        payload_hash=payload_hash,
        payload=payload,
        headers=_safe_headers(provider, request, validation.get("signature") or {}),
        validation=validation,
        received_at=_now(),
        notes=notes,
    )


@router.get("/status")
async def webhook_suite_status(project_slug: Optional[str] = None):
    if project_slug:
        return {"ok": True, "snapshot": webhook_snapshot(project_slug=project_slug.strip().lower())}
    snapshots = {project.slug: webhook_snapshot(project_slug=project.slug) for project in list_projects()}
    return {
        "ok": True,
        "projects": snapshots,
        "routes": {
            "suite_status": "/webhooks/status",
            "project_status": "/webhooks/status?project_slug=circa_haus",
            "recent_events": "/webhooks/events",
            "provider_project_ingest": "/webhooks/{provider}/{project_slug}",
        },
    }


@router.get("/events")
async def webhook_events(
    project_slug: Optional[str] = None,
    provider: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
):
    events = list_webhook_events(project_slug=project_slug, provider=provider, status=status, limit=limit)
    return {
        "ok": True,
        "count": len(events),
        "events": events,
    }


@router.post("/{provider}/{project_slug}")
async def ingest_webhook(
    provider: str,
    project_slug: str,
    request: Request,
    payload: Dict[str, Any] = Body(default_factory=dict),
):
    meta = extract_request_meta(request)
    normalized_provider = _normalized_provider(provider)
    normalized_project_slug = project_slug.strip().lower()
    raw_body = await request.body()
    validation = _validation_result(
        project_slug=normalized_project_slug,
        provider=normalized_provider,
        payload=payload,
        request=request,
        raw_body=raw_body,
    )
    payload_hash = canonical_payload_hash(payload)
    event_uid = make_event_uid(
        project_slug=normalized_project_slug,
        provider=normalized_provider,
        provider_event_id=validation.get("provider_event_id"),
        payload_hash=payload_hash,
    )

    project = get_project(normalized_project_slug)
    if project is None:
        stored = _persist_webhook_attempt(
            project_slug=normalized_project_slug,
            provider=normalized_provider,
            request=request,
            payload=payload,
            status="project_not_found",
            accepted=False,
            duplicate=False,
            validation=validation,
            notes="Project could not be resolved for webhook ingestion.",
        )
        audit_event(
            action="webhook.ingest",
            project_slug=normalized_project_slug,
            actor=meta.source,
            provider=normalized_provider,
            result="project_not_found",
            details={"webhook_event_id": stored.get("id"), "event_uid": event_uid},
        )
        return EtherErrorResponse.not_found(
            code="ETHER_PROJECT_NOT_FOUND",
            message="Project could not be resolved for webhook ingestion.",
            details={"project_slug": normalized_project_slug, "provider": normalized_provider, "webhook_event_id": stored.get("id")},
        )

    if _signature_should_reject(validation):
        stored = _persist_webhook_attempt(
            project_slug=project.slug,
            provider=normalized_provider,
            request=request,
            payload=payload,
            status="signature_invalid",
            accepted=False,
            duplicate=False,
            validation=validation,
            notes="Provider signature was configured but failed verification.",
        )
        audit_event(
            action="webhook.ingest",
            project_slug=project.slug,
            actor=meta.source,
            provider=normalized_provider,
            result="signature_invalid",
            details={"webhook_event_id": stored.get("id"), "event_uid": event_uid, "signature": validation.get("signature")},
        )
        return EtherErrorResponse.forbidden(
            code="ETHER_WEBHOOK_SIGNATURE_INVALID",
            message="Provider webhook signature failed verification.",
            details={"project_slug": project.slug, "provider": normalized_provider, "webhook_event_id": stored.get("id")},
        )

    if event_exists(event_uid):
        stored = _persist_webhook_attempt(
            project_slug=project.slug,
            provider=normalized_provider,
            request=request,
            payload=payload,
            status="duplicate_verified" if validation.get("signature_verified") else "duplicate",
            accepted=True,
            duplicate=True,
            validation=validation,
            notes="Duplicate provider event detected and idempotently accepted.",
        )
        audit_event(
            action="webhook.ingest",
            project_slug=project.slug,
            actor=meta.source,
            provider=normalized_provider,
            result="duplicate_verified" if validation.get("signature_verified") else "duplicate",
            details={"webhook_event_id": stored.get("id"), "event_uid": event_uid},
        )
        return {
            "ok": True,
            "accepted": True,
            "duplicate": True,
            "trusted": bool(validation.get("signature_verified")),
            "project_slug": project.slug,
            "provider": normalized_provider,
            "webhook_event_id": stored.get("id"),
            "event_uid": event_uid,
        }

    if control_plane_state.project_disabled(project.slug):
        stored = _persist_webhook_attempt(
            project_slug=project.slug,
            provider=normalized_provider,
            request=request,
            payload=payload,
            status="project_disabled",
            accepted=False,
            duplicate=False,
            validation=validation,
            notes="Project is disabled by Ether control plane.",
        )
        audit_event(
            action="webhook.ingest",
            project_slug=project.slug,
            actor=meta.source,
            provider=normalized_provider,
            result="project_disabled",
            details={"webhook_event_id": stored.get("id"), "event_uid": event_uid},
        )
        return EtherErrorResponse.forbidden(
            code="ETHER_PROJECT_DISABLED",
            message="Project is currently disabled by Ether control state.",
            details={"project_slug": project.slug, "provider": normalized_provider, "webhook_event_id": stored.get("id")},
        )

    if control_plane_state.provider_disabled(project.slug, normalized_provider):
        stored = _persist_webhook_attempt(
            project_slug=project.slug,
            provider=normalized_provider,
            request=request,
            payload=payload,
            status="provider_disabled_by_control",
            accepted=False,
            duplicate=False,
            validation=validation,
            notes="Provider is disabled by Ether control plane.",
        )
        audit_event(
            action="webhook.ingest",
            project_slug=project.slug,
            actor=meta.source,
            provider=normalized_provider,
            result="provider_disabled_by_control",
            details={"webhook_event_id": stored.get("id"), "event_uid": event_uid},
        )
        return EtherErrorResponse.forbidden(
            code="ETHER_PROVIDER_DISABLED_BY_CONTROL",
            message="Provider is currently disabled by Ether control state.",
            details={"project_slug": project.slug, "provider": normalized_provider, "webhook_event_id": stored.get("id")},
        )

    if not provider_enabled(project.slug, normalized_provider):
        stored = _persist_webhook_attempt(
            project_slug=project.slug,
            provider=normalized_provider,
            request=request,
            payload=payload,
            status="provider_not_enabled",
            accepted=False,
            duplicate=False,
            validation=validation,
            notes="Provider is not enabled for this project registry.",
        )
        audit_event(
            action="webhook.ingest",
            project_slug=project.slug,
            actor=meta.source,
            provider=normalized_provider,
            result="provider_not_enabled",
            details={"webhook_event_id": stored.get("id"), "event_uid": event_uid},
        )
        return EtherErrorResponse.forbidden(
            code="ETHER_PROVIDER_DISABLED",
            message="Provider is not enabled for this project.",
            details={"project_slug": project.slug, "provider": normalized_provider, "webhook_event_id": stored.get("id")},
        )

    configured_route = project.webhook_routes.get(normalized_provider)
    if validation.get("signature_verified"):
        status = "accepted_verified"
    elif validation.get("warnings"):
        status = "accepted_with_warnings"
    else:
        status = "accepted"
    stored = _persist_webhook_attempt(
        project_slug=project.slug,
        provider=normalized_provider,
        request=request,
        payload=payload,
        status=status,
        accepted=True,
        duplicate=False,
        validation=validation,
        notes="Webhook accepted into Ether provider operations store.",
    )
    audit_event(
        action="webhook.ingest",
        project_slug=project.slug,
        actor=meta.source,
        provider=normalized_provider,
        result=status,
        details={
            "webhook_event_id": stored.get("id"),
            "event_uid": event_uid,
            "trusted": bool(validation.get("signature_verified")),
            "configured_route": configured_route,
            "event_type": validation.get("event_type"),
            "provider_event_id": validation.get("provider_event_id"),
            "warnings": validation.get("warnings"),
            "payload_keys": sorted(list(payload.keys()))[:20],
        },
    )

    return {
        "ok": True,
        "accepted": True,
        "trusted": bool(validation.get("signature_verified")),
        "duplicate": False,
        "project_slug": project.slug,
        "provider": normalized_provider,
        "configured_route": configured_route,
        "webhook_event_id": stored.get("id"),
        "event_uid": event_uid,
        "event_type": validation.get("event_type"),
        "provider_event_id": validation.get("provider_event_id"),
        "validation": validation,
    }
