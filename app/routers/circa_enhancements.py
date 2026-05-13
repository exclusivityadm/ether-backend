from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from supabase import create_client

from app.utils.audit import audit_event
from app.utils.request_meta import extract_request_meta

log = logging.getLogger("ether_v2.circa_enhancements")

router = APIRouter(prefix="/circa", tags=["circa-enhancements"])

PROTECTED_REFERENCE_TERMS = {
    "nike",
    "adidas",
    "gucci",
    "louis vuitton",
    "chanel",
    "disney",
    "marvel",
    "dc comics",
    "pokemon",
    "hello kitty",
    "barbie",
    "star wars",
    "batman",
    "spider-man",
    "spiderman",
    "mickey",
    "superman",
}

CELEBRITY_REFERENCE_TERMS = {
    "celebrity likeness",
    "famous person",
    "look like beyonce",
    "look like taylor swift",
    "look like drake",
    "look like rihanna",
}

GENERAL_ECOMMERCE_BOUNDARIES = {
    "theme_marketplace": False,
    "pos": False,
    "marketplace_syndication": False,
    "plugin_ecosystem": False,
    "external_storefront_complexity": False,
    "custom_general_ecommerce_infrastructure": False,
}

CREATOR_COMMERCE_SURFACES = [
    "creator_profile_shop_tab",
    "campaign_page",
    "fan_club_post",
    "fan_club_exclusive_drop",
    "post_donation_upgrade_flow",
    "qr_landing_page",
    "promo_studio_export",
    "public_creator_link_in_bio_page",
]

LICENSED_AUDIO_SURFACES = [
    "campaigns",
    "fan_club_posts",
    "promo_studio_exports",
    "paid_or_monetized_content",
    "off_platform_posting",
]


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
            "attempted": False,
            "configured": False,
            "ok": False,
            "table": table,
            "error": "CIRCA_HAUS_SUPABASE_URL or CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY is not configured in Ether.",
        }
    try:
        response = client.table(table).insert(payload).execute()
        rows = getattr(response, "data", None) or []
        return {
            "attempted": True,
            "configured": True,
            "ok": True,
            "table": table,
            "rows": rows,
        }
    except Exception as exc:
        log.warning("circa_enhancement_insert_failed table=%s error=%s", table, _safe_error(exc))
        return {
            "attempted": True,
            "configured": True,
            "ok": False,
            "table": table,
            "error": _safe_error(exc),
        }


def _update(table: str, row_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    client = _supabase_client()
    if client is None:
        return {
            "attempted": False,
            "configured": False,
            "ok": False,
            "table": table,
            "error": "CIRCA_HAUS_SUPABASE_URL or CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY is not configured in Ether.",
        }
    try:
        response = client.table(table).update(payload).eq("id", row_id).execute()
        rows = getattr(response, "data", None) or []
        return {
            "attempted": True,
            "configured": True,
            "ok": True,
            "table": table,
            "rows": rows,
        }
    except Exception as exc:
        log.warning("circa_enhancement_update_failed table=%s error=%s", table, _safe_error(exc))
        return {
            "attempted": True,
            "configured": True,
            "ok": False,
            "table": table,
            "error": _safe_error(exc),
        }


def _scan_reference_risk(text: str) -> Dict[str, Any]:
    normalized = (text or "").lower()
    protected_hits = sorted([term for term in PROTECTED_REFERENCE_TERMS if term in normalized])
    celebrity_hits = sorted([term for term in CELEBRITY_REFERENCE_TERMS if term in normalized])
    risk_hits = protected_hits + celebrity_hits
    risk_level = "blocked_review" if risk_hits else "normal"
    warnings: List[str] = []
    if protected_hits:
        warnings.append("Prompt references protected brands, characters, logos, or existing IP. Saia must redirect to original creator-specific concepts.")
    if celebrity_hits:
        warnings.append("Prompt references a celebrity or real-person likeness. Saia must avoid generating or implying endorsement/likeness use.")
    if not warnings:
        warnings.append("No obvious protected-brand, character, or celebrity reference was detected. Rights attestation is still required before publish.")
    return {
        "risk_level": risk_level,
        "protected_reference_hits": protected_hits,
        "celebrity_reference_hits": celebrity_hits,
        "warnings": warnings,
    }


class RightsAttestationRequest(BaseModel):
    user_id: UUID
    creator_id: Optional[UUID] = None
    surface: str
    target_table: Optional[str] = None
    target_id: Optional[UUID] = None
    rights_summary: str = Field(default="", max_length=4000)
    saia_warning_shown: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CopyrightClaimRequest(BaseModel):
    claimant_name: Optional[str] = None
    claimant_email: Optional[str] = None
    reporter_user_id: Optional[UUID] = None
    accused_user_id: Optional[UUID] = None
    target_surface: str
    target_table: Optional[str] = None
    target_id: Optional[UUID] = None
    claim_summary: str = Field(default="", max_length=8000)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MerchIdeationRequest(BaseModel):
    creator_id: UUID
    campaign_id: Optional[UUID] = None
    fan_club_plan_id: Optional[UUID] = None
    prompt: str = Field(default="", max_length=8000)
    brand_direction: Dict[str, Any] = Field(default_factory=dict)
    audience_notes: Optional[str] = Field(default=None, max_length=4000)
    tone_notes: Optional[str] = Field(default=None, max_length=4000)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MerchConceptRequest(BaseModel):
    ideation_session_id: UUID
    creator_id: UUID
    concept_title: Optional[str] = Field(default=None, max_length=240)
    prompt: str = Field(default="", max_length=8000)
    storage_path: Optional[str] = None
    public_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MerchConceptApprovalRequest(BaseModel):
    concept_asset_id: UUID
    creator_id: UUID
    rights_attestation_id: Optional[UUID] = None
    merch_listing_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MerchPreflightRequest(BaseModel):
    creator_id: UUID
    concept_asset_id: Optional[UUID] = None
    merch_listing_asset_id: Optional[UUID] = None
    provider: Optional[str] = None
    product_type: Optional[str] = None
    print_area: Optional[str] = None
    resolution_passed: Optional[bool] = None
    placement_passed: Optional[bool] = None
    provider_constraints_passed: Optional[bool] = None
    rights_attestation_passed: Optional[bool] = None
    notes: Optional[str] = Field(default=None, max_length=4000)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreatorShopRequest(BaseModel):
    creator_id: UUID
    slug: Optional[str] = None
    title: str = "Creator Shop"
    status: str = "draft"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreatorShopItemRequest(BaseModel):
    shop_id: UUID
    creator_id: UUID
    merch_listing_id: UUID
    placement: str = "profile_shop_tab"
    status: str = "draft"
    display_order: int = 0
    campaign_id: Optional[UUID] = None
    fan_club_plan_id: Optional[UUID] = None
    qr_code_id: Optional[UUID] = None
    exclusive_audience: str = "public"
    limited_drop: bool = False
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AudioLicenseVerificationRequest(BaseModel):
    provider: str
    creator_id: Optional[UUID] = None
    campaign_id: Optional[UUID] = None
    fan_club_plan_id: Optional[UUID] = None
    promo_project_id: Optional[UUID] = None
    surface: str
    use_case: str
    license_reference: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.get("/enhanced/scope")
async def enhanced_scope(request: Request):
    meta = extract_request_meta(request)
    audit_event(action="circa.enhanced.scope", project_slug="circa_haus", actor=meta.source, result="ok")
    return {
        "ok": True,
        "project_slug": "circa_haus",
        "manual_auth_item": {
            "name": "Supabase Auth leaked-password protection",
            "can_be_done_by_connector": False,
            "reason": "The available Supabase connector exposes database, edge function, keys, logs, and advisors, but not the dashboard Auth leaked-password toggle.",
        },
        "enhanced_functionality": {
            "licensed_audio": {
                "native_ai_music_generation_at_launch": False,
                "providers": ["epidemic_sound", "artlist"],
                "surfaces": LICENSED_AUDIO_SURFACES,
                "launch_inclusion": "conditional_on_api_partner_access_licensing_scope_cost_and_usage_right_verification",
            },
            "saia_rights_guidance": {
                "content_id_style_detection_at_launch": False,
                "supported": [
                    "rights_intake",
                    "license_metadata_checks",
                    "attestation_enforcement",
                    "risk_surface_warnings",
                    "copyright_claim_workflow_support",
                    "repeat_or_knowing_violation_escalation_cues",
                ],
            },
            "merch_studio_creator_shop": {
                "commerce_model": "creator_native_commerce_not_shopify_clone",
                "surfaces": CREATOR_COMMERCE_SURFACES,
                "excluded_general_ecommerce_features": GENERAL_ECOMMERCE_BOUNDARIES,
            },
            "saia_merch_ideation": {
                "enabled_by_contract": True,
                "requires_creator_approval_before_publish": True,
                "requires_rights_attestation": True,
                "requires_provider_safe_preflight": True,
                "no_silent_generation_and_publish": True,
            },
        },
    }


@router.post("/rights/attestations")
async def create_rights_attestation(payload: RightsAttestationRequest, request: Request):
    meta = extract_request_meta(request)
    record = payload.model_dump(mode="json")
    record["risk_level"] = "normal"
    record["status"] = "attested"
    result = _insert("rights_attestations", record)
    audit_event(
        action="circa.rights_attestation.create",
        project_slug="circa_haus",
        actor=meta.source,
        result="ok" if result.get("ok") else "pending_configuration",
        details={"surface": payload.surface, "target_table": payload.target_table, "db": result},
    )
    return {"ok": bool(result.get("ok")), "record": record, "db": result}


@router.post("/rights/copyright-claims")
async def create_copyright_claim(payload: CopyrightClaimRequest, request: Request):
    meta = extract_request_meta(request)
    record = payload.model_dump(mode="json")
    record["claim_status"] = "received"
    result = _insert("copyright_claims", record)
    audit_event(
        action="circa.copyright_claim.create",
        project_slug="circa_haus",
        actor=meta.source,
        result="ok" if result.get("ok") else "pending_configuration",
        details={"surface": payload.target_surface, "target_table": payload.target_table, "db": result},
    )
    return {"ok": bool(result.get("ok")), "record": record, "db": result}


@router.post("/merch/ideation/sessions")
async def create_merch_ideation_session(payload: MerchIdeationRequest, request: Request):
    meta = extract_request_meta(request)
    risk = _scan_reference_risk(payload.prompt)
    record = payload.model_dump(mode="json")
    record["rights_warning_shown"] = True
    record["status"] = "needs_revision" if risk["risk_level"] == "blocked_review" else "draft"
    record["metadata"] = {**payload.metadata, "saia_reference_risk_scan": risk}
    result = _insert("merch_ideation_sessions", record)
    audit_event(
        action="circa.merch_ideation.session_create",
        project_slug="circa_haus",
        actor=meta.source,
        result="blocked_review" if risk["risk_level"] == "blocked_review" else ("ok" if result.get("ok") else "pending_configuration"),
        details={"risk": risk, "db": result},
    )
    return {
        "ok": bool(result.get("ok")) and risk["risk_level"] != "blocked_review",
        "requires_revision": risk["risk_level"] == "blocked_review",
        "risk": risk,
        "record": record,
        "db": result,
    }


@router.post("/merch/concepts")
async def create_merch_concept(payload: MerchConceptRequest, request: Request):
    meta = extract_request_meta(request)
    risk = _scan_reference_risk(payload.prompt)
    image_model_configured = bool(_env("CIRCA_HAUS_OPENAI_IMAGE_MODEL"))
    record = payload.model_dump(mode="json")
    record["concept_type"] = "image_concept"
    record["status"] = "needs_revision" if risk["risk_level"] == "blocked_review" else "generated_for_review"
    record["metadata"] = {
        **payload.metadata,
        "saia_reference_risk_scan": risk,
        "image_model_configured": image_model_configured,
        "generation_mode": "credentialed_provider_required" if not image_model_configured else "ready_for_provider_generation",
    }
    result = _insert("merch_concept_assets", record)
    audit_event(
        action="circa.merch_concept.create",
        project_slug="circa_haus",
        actor=meta.source,
        result="blocked_review" if risk["risk_level"] == "blocked_review" else ("ok" if result.get("ok") else "pending_configuration"),
        details={"risk": risk, "image_model_configured": image_model_configured, "db": result},
    )
    return {
        "ok": bool(result.get("ok")) and risk["risk_level"] != "blocked_review",
        "provider_generation_ready": image_model_configured,
        "requires_revision": risk["risk_level"] == "blocked_review",
        "risk": risk,
        "record": record,
        "db": result,
    }


@router.post("/merch/concepts/approve")
async def approve_merch_concept(payload: MerchConceptApprovalRequest, request: Request):
    meta = extract_request_meta(request)
    update_payload: Dict[str, Any] = {
        "selected_by_creator": True,
        "creator_approved_at": _utc_now(),
        "status": "creator_approved_pending_preflight",
        "metadata": payload.metadata,
    }
    if payload.rights_attestation_id:
        update_payload["rights_attestation_id"] = str(payload.rights_attestation_id)
    if payload.merch_listing_id:
        update_payload["merch_listing_id"] = str(payload.merch_listing_id)
    result = _update("merch_concept_assets", str(payload.concept_asset_id), update_payload)
    audit_event(
        action="circa.merch_concept.creator_approve",
        project_slug="circa_haus",
        actor=meta.source,
        result="ok" if result.get("ok") else "pending_configuration",
        details={"concept_asset_id": str(payload.concept_asset_id), "db": result},
    )
    return {"ok": bool(result.get("ok")), "update": update_payload, "db": result}


@router.post("/merch/preflight-reviews")
async def create_merch_preflight_review(payload: MerchPreflightRequest, request: Request):
    meta = extract_request_meta(request)
    passed = all(
        value is True
        for value in [
            payload.resolution_passed,
            payload.placement_passed,
            payload.provider_constraints_passed,
            payload.rights_attestation_passed,
        ]
    )
    record = payload.model_dump(mode="json")
    record["status"] = "passed" if passed else "needs_fix"
    record["reviewed_at"] = _utc_now()
    result = _insert("merch_artwork_preflight_reviews", record)
    audit_event(
        action="circa.merch_preflight.create",
        project_slug="circa_haus",
        actor=meta.source,
        result="passed" if passed else "needs_fix",
        details={"provider": payload.provider, "product_type": payload.product_type, "db": result},
    )
    return {"ok": bool(result.get("ok")), "passed": passed, "record": record, "db": result}


@router.post("/creator-shop")
async def create_creator_shop(payload: CreatorShopRequest, request: Request):
    meta = extract_request_meta(request)
    record = payload.model_dump(mode="json")
    record["shop_mode"] = "creator_native"
    record["general_ecommerce_features_enabled"] = False
    result = _insert("creator_shops", record)
    audit_event(
        action="circa.creator_shop.create",
        project_slug="circa_haus",
        actor=meta.source,
        result="ok" if result.get("ok") else "pending_configuration",
        details={"creator_id": str(payload.creator_id), "db": result},
    )
    return {"ok": bool(result.get("ok")), "record": record, "db": result}


@router.post("/creator-shop/items")
async def create_creator_shop_item(payload: CreatorShopItemRequest, request: Request):
    meta = extract_request_meta(request)
    record = payload.model_dump(mode="json")
    if record["placement"] not in CREATOR_COMMERCE_SURFACES:
        record["metadata"] = {
            **payload.metadata,
            "placement_warning": "Placement is not in the approved creator-native surface list. Review before publish.",
            "approved_surfaces": CREATOR_COMMERCE_SURFACES,
        }
        if record["status"] == "published":
            record["status"] = "draft"
    result = _insert("creator_shop_items", record)
    audit_event(
        action="circa.creator_shop_item.create",
        project_slug="circa_haus",
        actor=meta.source,
        result="ok" if result.get("ok") else "pending_configuration",
        details={"placement": record["placement"], "status": record["status"], "db": result},
    )
    return {"ok": bool(result.get("ok")), "record": record, "db": result}


@router.post("/audio/license-verifications")
async def create_audio_license_verification(payload: AudioLicenseVerificationRequest, request: Request):
    meta = extract_request_meta(request)
    provider = payload.provider.strip().lower()
    allowed_provider = provider in {"epidemic_sound", "artlist"}
    allowed_surface = payload.surface in LICENSED_AUDIO_SURFACES
    record = payload.model_dump(mode="json")
    record["provider"] = provider
    record["verification_status"] = "pending" if allowed_provider and allowed_surface else "needs_review"
    record["verified_by"] = "saia_rights_intake"
    record["metadata"] = {
        **payload.metadata,
        "native_ai_music_generation_at_launch": False,
        "allowed_provider": allowed_provider,
        "allowed_surface": allowed_surface,
        "allowed_surfaces": LICENSED_AUDIO_SURFACES,
    }
    result = _insert("audio_license_verifications", record)
    audit_event(
        action="circa.audio_license_verification.create",
        project_slug="circa_haus",
        actor=meta.source,
        provider=provider,
        result="ok" if result.get("ok") and allowed_provider and allowed_surface else "needs_review",
        details={"surface": payload.surface, "db": result},
    )
    return {
        "ok": bool(result.get("ok")) and allowed_provider and allowed_surface,
        "allowed_provider": allowed_provider,
        "allowed_surface": allowed_surface,
        "record": record,
        "db": result,
    }
