from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from supabase import create_client

from app.utils.audit import audit_event
from app.utils.request_meta import extract_request_meta

log = logging.getLogger("ether_v2.circa_premium")

router = APIRouter(prefix="/circa/premium", tags=["circa-premium"])

CREATOR_NATIVE_SURFACES = {
    "creator_profile_shop_tab",
    "campaign_page",
    "fan_club_post",
    "fan_club_exclusive_drop",
    "post_donation_upgrade_flow",
    "qr_landing_page",
    "promo_studio_export",
    "public_creator_link_in_bio_page",
}

GENERAL_ECOMMERCE_BLOCKED_FEATURES = {
    "theme_marketplace",
    "pos",
    "marketplace_syndication",
    "plugin_ecosystem",
    "external_storefront_complexity",
    "custom_general_ecommerce_infrastructure",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _env(name: str) -> Optional[str]:
    value = os.getenv(name, "").strip()
    return value or None


def _supabase_client():
    url = _env("CIRCA_HAUS_SUPABASE_URL")
    key = _env("CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


def _safe_error(exc: Exception) -> str:
    text = str(exc).strip() or exc.__class__.__name__
    return text[:240]


def _insert(table: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    client = _supabase_client()
    if client is None:
        return {
            "ok": False,
            "attempted": False,
            "configured": False,
            "table": table,
            "error": "CIRCA_HAUS_SUPABASE_URL or CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY is not configured in Ether.",
        }
    try:
        response = client.table(table).insert(payload).execute()
        return {"ok": True, "attempted": True, "configured": True, "table": table, "rows": getattr(response, "data", None) or []}
    except Exception as exc:
        log.warning("circa_premium_insert_failed table=%s error=%s", table, _safe_error(exc))
        return {"ok": False, "attempted": True, "configured": True, "table": table, "error": _safe_error(exc)}


def _update(table: str, row_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    client = _supabase_client()
    if client is None:
        return {
            "ok": False,
            "attempted": False,
            "configured": False,
            "table": table,
            "error": "CIRCA_HAUS_SUPABASE_URL or CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY is not configured in Ether.",
        }
    try:
        response = client.table(table).update(payload).eq("id", row_id).execute()
        return {"ok": True, "attempted": True, "configured": True, "table": table, "rows": getattr(response, "data", None) or []}
    except Exception as exc:
        log.warning("circa_premium_update_failed table=%s error=%s", table, _safe_error(exc))
        return {"ok": False, "attempted": True, "configured": True, "table": table, "error": _safe_error(exc)}


def _rpc(name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    client = _supabase_client()
    if client is None:
        return {
            "ok": False,
            "attempted": False,
            "configured": False,
            "rpc": name,
            "error": "CIRCA_HAUS_SUPABASE_URL or CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY is not configured in Ether.",
        }
    try:
        response = client.rpc(name, payload).execute()
        return {"ok": True, "attempted": True, "configured": True, "rpc": name, "data": getattr(response, "data", None)}
    except Exception as exc:
        log.warning("circa_premium_rpc_failed rpc=%s error=%s", name, _safe_error(exc))
        return {"ok": False, "attempted": True, "configured": True, "rpc": name, "error": _safe_error(exc)}


class SaiaMerchBriefRequest(BaseModel):
    creator_id: UUID
    campaign_id: Optional[UUID] = None
    fan_club_plan_id: Optional[UUID] = None
    brief_title: Optional[str] = Field(default=None, max_length=240)
    collection_goal: Optional[str] = Field(default=None, max_length=4000)
    brand_voice: Optional[str] = Field(default=None, max_length=2000)
    audience_summary: Optional[str] = Field(default=None, max_length=4000)
    visual_direction: Dict[str, Any] = Field(default_factory=dict)
    color_direction: Dict[str, Any] = Field(default_factory=dict)
    slogan_direction: Optional[str] = Field(default=None, max_length=2000)
    drop_strategy: Optional[str] = Field(default=None, max_length=2000)
    pricing_strategy: Optional[str] = Field(default=None, max_length=2000)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SaiaWorkflowEventRequest(BaseModel):
    creator_id: Optional[UUID] = None
    workflow_key: str
    step_key: str
    status: str = "started"
    target_table: Optional[str] = None
    target_id: Optional[UUID] = None
    requires_creator_confirmation: bool = False
    creator_confirmed: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MerchCollectionRequest(BaseModel):
    creator_id: UUID
    shop_id: Optional[UUID] = None
    campaign_id: Optional[UUID] = None
    fan_club_plan_id: Optional[UUID] = None
    title: str = Field(max_length=240)
    slug: Optional[str] = None
    description: Optional[str] = None
    collection_type: str = "standard"
    status: str = "draft"
    exclusive_audience: str = "public"
    limited_drop: bool = False
    quantity_limit: Optional[int] = None
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    cover_image_url: Optional[str] = None
    rights_attestation_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MerchCollectionItemRequest(BaseModel):
    collection_id: UUID
    creator_id: UUID
    merch_listing_id: UUID
    display_order: int = 0
    featured: bool = False
    status: str = "draft"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MerchDropWaitlistRequest(BaseModel):
    collection_id: Optional[UUID] = None
    merch_listing_id: Optional[UUID] = None
    creator_id: Optional[UUID] = None
    supporter_id: Optional[UUID] = None
    email: Optional[str] = None
    source_surface: Optional[str] = None
    qr_code_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CheckoutIntentRequest(BaseModel):
    creator_id: Optional[UUID] = None
    supporter_id: Optional[UUID] = None
    source_surface: str
    source_ref_id: Optional[UUID] = None
    currency: str = "usd"
    subtotal_cents: int = 0
    estimated_tax_cents: int = 0
    estimated_shipping_cents: int = 0
    total_cents: int = 0
    donation_id: Optional[UUID] = None
    qr_code_id: Optional[UUID] = None
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PremiumAnalyticsEventRequest(BaseModel):
    creator_id: Optional[UUID] = None
    supporter_id: Optional[UUID] = None
    shop_id: Optional[UUID] = None
    collection_id: Optional[UUID] = None
    merch_listing_id: Optional[UUID] = None
    event_type: str
    source_surface: Optional[str] = None
    session_id: Optional[str] = None
    qr_code_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LicensedAudioPlacementRequest(BaseModel):
    audio_license_verification_id: Optional[UUID] = None
    provider: str
    creator_id: Optional[UUID] = None
    promo_project_id: Optional[UUID] = None
    campaign_id: Optional[UUID] = None
    fan_club_plan_id: Optional[UUID] = None
    surface: str
    off_platform_destination: Optional[str] = None
    usage_rights_verified: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PublishReadyRequest(BaseModel):
    merch_listing_id: UUID


@router.get("/scope")
async def premium_scope(request: Request):
    meta = extract_request_meta(request)
    audit_event(action="circa.premium.scope", project_slug="circa_haus", actor=meta.source, result="ok")
    return {
        "ok": True,
        "premium_experience": {
            "saia_guided_merch_briefs": True,
            "creator_shop_collections": True,
            "limited_drops_and_waitlist": True,
            "unified_checkout_intents": True,
            "analytics_events": True,
            "licensed_audio_placements": True,
            "provider_print_profiles": True,
            "publish_readiness_checks": True,
        },
        "creator_native_surfaces": sorted(CREATOR_NATIVE_SURFACES),
        "blocked_general_ecommerce_features": sorted(GENERAL_ECOMMERCE_BLOCKED_FEATURES),
    }


@router.post("/saia/merch-briefs")
async def create_saia_merch_brief(payload: SaiaMerchBriefRequest, request: Request):
    meta = extract_request_meta(request)
    record = payload.model_dump(mode="json")
    record["rights_warning_shown"] = True
    result = _insert("saia_merch_briefs", record)
    audit_event(action="circa.premium.saia_merch_brief.create", project_slug="circa_haus", actor=meta.source, result="ok" if result.get("ok") else "pending_configuration", details={"db": result})
    return {"ok": bool(result.get("ok")), "record": record, "db": result}


@router.post("/saia/workflow-events")
async def create_saia_workflow_event(payload: SaiaWorkflowEventRequest, request: Request):
    meta = extract_request_meta(request)
    record = payload.model_dump(mode="json", exclude={"creator_confirmed"})
    if payload.creator_confirmed:
        record["creator_confirmed_at"] = _utc_now()
    result = _insert("saia_workflow_events", record)
    audit_event(action="circa.premium.saia_workflow_event.create", project_slug="circa_haus", actor=meta.source, result="ok" if result.get("ok") else "pending_configuration", details={"workflow_key": payload.workflow_key, "step_key": payload.step_key, "db": result})
    return {"ok": bool(result.get("ok")), "record": record, "db": result}


@router.post("/collections")
async def create_merch_collection(payload: MerchCollectionRequest, request: Request):
    meta = extract_request_meta(request)
    record = payload.model_dump(mode="json")
    if payload.status == "published" and not payload.rights_attestation_id:
        record["status"] = "draft"
        record["metadata"] = {**payload.metadata, "publish_blocker": "rights_attestation_required_before_publish"}
    if payload.status == "published" and payload.rights_attestation_id:
        record["approved_by_creator_at"] = _utc_now()
        record["published_at"] = _utc_now()
    result = _insert("merch_collections", record)
    audit_event(action="circa.premium.collection.create", project_slug="circa_haus", actor=meta.source, result="ok" if result.get("ok") else "pending_configuration", details={"status": record.get("status"), "db": result})
    return {"ok": bool(result.get("ok")), "record": record, "db": result}


@router.post("/collections/items")
async def create_merch_collection_item(payload: MerchCollectionItemRequest, request: Request):
    meta = extract_request_meta(request)
    record = payload.model_dump(mode="json")
    result = _insert("merch_collection_items", record)
    audit_event(action="circa.premium.collection_item.create", project_slug="circa_haus", actor=meta.source, result="ok" if result.get("ok") else "pending_configuration", details={"collection_id": str(payload.collection_id), "db": result})
    return {"ok": bool(result.get("ok")), "record": record, "db": result}


@router.post("/drops/waitlist")
async def join_merch_drop_waitlist(payload: MerchDropWaitlistRequest, request: Request):
    meta = extract_request_meta(request)
    record = payload.model_dump(mode="json")
    record["status"] = "waiting"
    result = _insert("merch_drop_waitlist", record)
    audit_event(action="circa.premium.drop_waitlist.join", project_slug="circa_haus", actor=meta.source, result="ok" if result.get("ok") else "pending_configuration", details={"source_surface": payload.source_surface, "db": result})
    return {"ok": bool(result.get("ok")), "record": record, "db": result}


@router.post("/checkout/intents")
async def create_checkout_intent(payload: CheckoutIntentRequest, request: Request):
    meta = extract_request_meta(request)
    record = payload.model_dump(mode="json")
    if payload.source_surface not in CREATOR_NATIVE_SURFACES:
        record["metadata"] = {**payload.metadata, "surface_warning": "Source surface is outside the approved creator-native commerce surfaces."}
    result = _insert("commerce_checkout_intents", record)
    audit_event(action="circa.premium.checkout_intent.create", project_slug="circa_haus", actor=meta.source, result="ok" if result.get("ok") else "pending_configuration", details={"source_surface": payload.source_surface, "db": result})
    return {"ok": bool(result.get("ok")), "record": record, "db": result}


@router.post("/analytics/events")
async def record_premium_analytics_event(payload: PremiumAnalyticsEventRequest, request: Request):
    meta = extract_request_meta(request)
    rpc_payload = payload.model_dump(mode="json")
    result = _rpc("circa_record_premium_event", {"payload": rpc_payload})
    audit_event(action="circa.premium.analytics_event.record", project_slug="circa_haus", actor=meta.source, result="ok" if result.get("ok") else "pending_configuration", details={"event_type": payload.event_type, "db": result})
    return {"ok": bool(result.get("ok")), "payload": rpc_payload, "db": result}


@router.post("/audio/placements")
async def create_licensed_audio_placement(payload: LicensedAudioPlacementRequest, request: Request):
    meta = extract_request_meta(request)
    provider = payload.provider.strip().lower()
    record = payload.model_dump(mode="json")
    record["provider"] = provider
    record["placement_status"] = "verified" if payload.usage_rights_verified else "pending_verification"
    record["metadata"] = {**payload.metadata, "native_ai_music_generation_at_launch": False}
    result = _insert("licensed_audio_placements", record)
    audit_event(action="circa.premium.audio_placement.create", project_slug="circa_haus", actor=meta.source, provider=provider, result="ok" if result.get("ok") else "pending_configuration", details={"surface": payload.surface, "status": record["placement_status"], "db": result})
    return {"ok": bool(result.get("ok")), "record": record, "db": result}


@router.post("/merch/publish-ready")
async def merch_publish_ready(payload: PublishReadyRequest, request: Request):
    meta = extract_request_meta(request)
    result = _rpc("circa_shop_publish_ready", {"p_merch_listing_id": str(payload.merch_listing_id)})
    audit_event(action="circa.premium.merch_publish_ready", project_slug="circa_haus", actor=meta.source, result="ok" if result.get("ok") else "pending_configuration", details={"merch_listing_id": str(payload.merch_listing_id), "db": result})
    return {"ok": bool(result.get("ok")), "db": result}
