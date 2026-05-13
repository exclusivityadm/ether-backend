from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.utils.settings import settings

log = logging.getLogger("ether_v2.projects")


class ProjectRecord(BaseModel):
    slug: str
    display_name: str
    status: str = "planned"
    environment: str = "development"

    app_domains: List[str] = Field(default_factory=list)
    admin_domains: List[str] = Field(default_factory=list)
    app_ids: List[str] = Field(default_factory=list)
    bundle_ids: List[str] = Field(default_factory=list)

    provider_set: Dict[str, bool] = Field(default_factory=dict)
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    branding: Dict[str, Any] = Field(default_factory=dict)
    allowed_roles: List[str] = Field(default_factory=list)
    admin_surface_id: Optional[str] = None
    webhook_routes: Dict[str, str] = Field(default_factory=dict)

    supabase_url: Optional[str] = None
    supabase_anon_key_configured: bool = False
    service_role_configured: bool = False
    signal_secret_configured: bool = False
    signal_secret_value: Optional[str] = None


def _project_env(prefix_slug: str, suffix: str) -> Optional[str]:
    key = f"{prefix_slug.strip().upper()}_{suffix.strip().upper()}"
    value = os.getenv(key, "").strip()
    return value or None


def _enrich_project_secrets(payload: Dict[str, Any]) -> Dict[str, Any]:
    slug = str(payload.get("slug", "")).strip().upper()
    if not slug:
        return dict(payload)

    supabase_url = _project_env(slug, "SUPABASE_URL")
    anon_key = _project_env(slug, "SUPABASE_ANON_KEY")
    service_role_key = _project_env(slug, "SUPABASE_SERVICE_ROLE_KEY")
    signal_secret = _project_env(slug, "ETHER_SIGNAL_SECRET") or _project_env(slug, "SIGNAL_SECRET")

    enriched = dict(payload)
    if supabase_url:
        enriched["supabase_url"] = supabase_url
    enriched["supabase_anon_key_configured"] = bool(anon_key)
    enriched["service_role_configured"] = bool(service_role_key)
    enriched["signal_secret_configured"] = bool(signal_secret)
    enriched["signal_secret_value"] = signal_secret
    return enriched


def _default_projects() -> List[Dict[str, Any]]:
    return [
        {
            "slug": "circa_haus",
            "display_name": "Circa Haus",
            "status": "launch_preparation",
            "environment": settings.ETHER_ENVIRONMENT,
            "app_ids": ["circa_haus"],
            "provider_set": {
                "supabase": True,
                "stripe": True,
                "openai": True,
                "elevenlabs": True,
                "canva": True,
                "apliiq": True,
                "printful": True,
                "cloudflare": True,
                "google_workspace": True,
                "amazon_ses": True,
                "twilio": True,
            },
            "feature_flags": {
                "ether_fronted": False,
                "rebrand_required": False,
                "provider_wiring_pending": True,
                "sentinel_enabled": True,
                "signal_lane_supported": True,
                "keepalive_supported": True,
                "campaign_builder_supported": True,
                "promo_studio_supported": True,
                "merch_studio_supported": True,
                "fan_club_supported": True,
                "qr_routing_supported": True,
                "admin_launch_console_supported": True,
            },
            "branding": {
                "app_name": "Circa Haus",
                "tagline": "The trusted home for creator independence",
                "ai_name": "Saia",
                "ai_positioning": "Co-Captain",
                "identity": "circa-haus-luxury-navy-gold",
            },
            "allowed_roles": ["supporter", "creator", "admin"],
            "admin_surface_id": "circa-haus-admin",
            "webhook_routes": {
                "stripe": "/webhooks/stripe/circa_haus",
                "twilio": "/webhooks/twilio/circa_haus",
                "canva": "/webhooks/canva/circa_haus",
                "apliiq": "/webhooks/apliiq/circa_haus",
                "printful": "/webhooks/printful/circa_haus",
            },
        },
        {
            "slug": "exclusivity",
            "display_name": "Exclusivity",
            "status": "active",
            "environment": settings.ETHER_ENVIRONMENT,
            "app_ids": ["exclusivity"],
            "provider_set": {
                "supabase": True,
                "stripe": False,
                "twilio": False,
                "openai": False,
                "elevenlabs": False,
            },
            "feature_flags": {
                "legacy_ingest_enabled": True,
                "sentinel_enabled": True,
                "signal_lane_supported": True,
                "keepalive_supported": True,
            },
            "branding": {
                "app_name": "Exclusivity",
            },
            "allowed_roles": ["merchant", "admin"],
            "admin_surface_id": "exclusivity-admin",
            "webhook_routes": {},
        },
        {
            "slug": "sova",
            "display_name": "Sova",
            "status": "planned",
            "environment": settings.ETHER_ENVIRONMENT,
            "app_ids": ["sova"],
            "provider_set": {
                "supabase": True,
                "stripe": False,
                "twilio": False,
                "openai": False,
                "elevenlabs": False,
            },
            "feature_flags": {
                "legacy_ingest_enabled": True,
                "sentinel_enabled": True,
                "signal_lane_supported": True,
                "keepalive_supported": True,
            },
            "branding": {
                "app_name": "Sova",
            },
            "allowed_roles": ["merchant", "admin"],
            "admin_surface_id": "sova-admin",
            "webhook_routes": {},
        },
    ]


def _coerce_project_entries(raw: Any) -> Dict[str, Dict[str, Any]]:
    if raw is None:
        return {}

    items: List[Dict[str, Any]] = []
    if isinstance(raw, list):
        items = [item for item in raw if isinstance(item, dict)]
    elif isinstance(raw, dict):
        for slug, item in raw.items():
            if isinstance(item, dict):
                items.append({"slug": slug, **item})

    result: Dict[str, Dict[str, Any]] = {}
    for item in items:
        slug = str(item.get("slug", "")).strip().lower()
        if not slug:
            continue
        result[slug] = {**item, "slug": slug}
    return result


def _deep_merge_project_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for nested_key in ("provider_set", "feature_flags", "branding", "webhook_routes"):
        if isinstance(base.get(nested_key), dict) and isinstance(override.get(nested_key), dict):
            merged[nested_key] = {**base.get(nested_key, {}), **override.get(nested_key, {})}

    for nested_key in ("allowed_roles", "app_domains", "admin_domains", "app_ids", "bundle_ids"):
        if nested_key in override and isinstance(override.get(nested_key), list):
            merged[nested_key] = list(override[nested_key])

    for key, value in override.items():
        if key in {"provider_set", "feature_flags", "branding", "webhook_routes", "allowed_roles", "app_domains", "admin_domains", "app_ids", "bundle_ids"}:
            continue
        merged[key] = value
    return merged


@lru_cache(maxsize=1)
def get_project_registry() -> Dict[str, ProjectRecord]:
    registry: Dict[str, ProjectRecord] = {
        item["slug"]: ProjectRecord.model_validate(_enrich_project_secrets(item)) for item in _default_projects()
    }

    raw = (settings.ETHER_PROJECTS_JSON or "").strip()
    if not raw:
        return registry

    try:
        overrides = _coerce_project_entries(json.loads(raw))
    except json.JSONDecodeError:
        log.warning("Ignoring invalid ETHER_PROJECTS_JSON; failed to parse JSON.")
        return registry

    for slug, payload in overrides.items():
        payload = _enrich_project_secrets(payload)
        if slug in registry:
            merged = _deep_merge_project_dict(registry[slug].model_dump(), payload)
            registry[slug] = ProjectRecord.model_validate(merged)
        else:
            registry[slug] = ProjectRecord.model_validate(payload)

    return registry


def list_projects() -> List[ProjectRecord]:
    return sorted(get_project_registry().values(), key=lambda item: item.slug)


def get_project(project_slug: str) -> Optional[ProjectRecord]:
    if not project_slug:
        return None
    return get_project_registry().get(project_slug.strip().lower())


def resolve_project(
    project_slug: Optional[str] = None,
    source: Optional[str] = None,
    app_domain: Optional[str] = None,
    admin_domain: Optional[str] = None,
    bundle_id: Optional[str] = None,
    app_id: Optional[str] = None,
) -> Optional[ProjectRecord]:
    registry = get_project_registry()

    direct_candidates = [
        (project_slug or "").strip().lower(),
        (source or "").strip().lower(),
        (app_id or "").strip().lower(),
    ]
    for candidate in direct_candidates:
        if candidate and candidate in registry:
            return registry[candidate]

    app_domain = (app_domain or "").strip().lower()
    admin_domain = (admin_domain or "").strip().lower()
    bundle_id = (bundle_id or "").strip().lower()

    for project in registry.values():
        if app_domain and app_domain in {value.lower() for value in project.app_domains}:
            return project
        if admin_domain and admin_domain in {value.lower() for value in project.admin_domains}:
            return project
        if bundle_id and bundle_id in {value.lower() for value in project.bundle_ids}:
            return project
        if app_id and app_id in {value.lower() for value in project.app_ids}:
            return project

    return None


def project_to_public_payload(project: ProjectRecord) -> Dict[str, Any]:
    payload = project.model_dump(
        exclude={
            "supabase_url",
            "supabase_anon_key_configured",
            "service_role_configured",
            "signal_secret_value",
        }
    )
    enabled_providers = sorted([name for name, enabled in project.provider_set.items() if enabled])
    payload["enabled_providers"] = enabled_providers
    payload["supabase_ready"] = bool(project.supabase_url and project.supabase_anon_key_configured)
    payload["signal_ready"] = bool(project.signal_secret_configured)
    payload["signal"] = {
        "handshake_path": "/signal/handshake",
        "heartbeat_path": "/signal/heartbeat",
        "lanes_path": "/signal/lanes",
        "proof_required": bool(project.signal_secret_configured),
        "next_heartbeat_seconds": 60,
    }

    if settings.ETHER_BOOTSTRAP_EXPOSE_PUBLIC_CONFIG and project.supabase_url:
        payload["public_config"] = {
            "supabase_url": project.supabase_url,
        }

    return payload
