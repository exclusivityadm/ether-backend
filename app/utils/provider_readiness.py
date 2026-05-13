from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List

from app.utils.control_plane import control_plane_state
from app.utils.project_supabase_signal import project_signal_readiness
from app.utils.projects import get_project, list_projects
from app.utils.webhook_signature import signature_readiness_for_project


@dataclass(frozen=True)
class ProviderReadinessResult:
    provider: str
    enabled: bool
    disabled_by_control_plane: bool
    configured: bool
    signature_configured: bool
    signature_required_for_launch: bool
    required_for_launch: bool
    launch_blocking: bool
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


CIRCA_HAUS_LAUNCH_REQUIRED = {
    "supabase",
    "stripe",
    "openai",
    "elevenlabs",
    "canva",
    "apliiq",
    "printful",
    "cloudflare",
    "google_workspace",
    "amazon_ses",
    "twilio",
    "saia_merch_ideation",
    "saia_rights_guidance",
}

# Planned/conditional providers are tracked, but they do not block launch until official
# API/partner access, licensing scope, cost, and verifiable usage rights are confirmed.
CIRCA_HAUS_CONDITIONAL_PROVIDERS = {
    "epidemic_sound",
    "artlist",
}

EXCLUSIVITY_LAUNCH_REQUIRED = {
    "supabase",
}

# Incoming provider events that can affect money movement, messaging, design publishing,
# fulfillment, or user state must have webhook trust configured before live launch.
CIRCA_HAUS_SIGNATURE_REQUIRED = {
    "stripe",
    "twilio",
    "canva",
    "apliiq",
    "printful",
}

EXCLUSIVITY_SIGNATURE_REQUIRED = set()

PROVIDER_ENV_REQUIREMENTS: Dict[str, Dict[str, List[str]]] = {
    "circa_haus": {
        "supabase": [
            "CIRCA_HAUS_SUPABASE_URL",
            "CIRCA_HAUS_SUPABASE_ANON_KEY",
            "CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY",
            "CIRCA_HAUS_ETHER_SIGNAL_SECRET",
        ],
        "stripe": [
            "CIRCA_HAUS_STRIPE_PUBLISHABLE_KEY",
            "CIRCA_HAUS_STRIPE_SECRET_KEY",
            "CIRCA_HAUS_STRIPE_WEBHOOK_SECRET",
            "CIRCA_HAUS_STRIPE_CONNECT_CLIENT_ID",
            "CIRCA_HAUS_STRIPE_PLATFORM_FEE_BPS",
        ],
        "openai": [
            "CIRCA_HAUS_OPENAI_API_KEY",
            "CIRCA_HAUS_OPENAI_MODEL",
            "CIRCA_HAUS_OPENAI_IMAGE_MODEL",
        ],
        "saia_merch_ideation": [
            "CIRCA_HAUS_OPENAI_API_KEY",
            "CIRCA_HAUS_OPENAI_IMAGE_MODEL",
            "CIRCA_HAUS_SAIA_MERCH_IDEATION_ENABLED",
        ],
        "saia_rights_guidance": [
            "CIRCA_HAUS_OPENAI_API_KEY",
            "CIRCA_HAUS_SAIA_RIGHTS_GUIDANCE_ENABLED",
        ],
        "elevenlabs": [
            "CIRCA_HAUS_ELEVENLABS_API_KEY",
            "CIRCA_HAUS_ELEVENLABS_TALETHIA_VOICE_ID",
            "CIRCA_HAUS_ELEVENLABS_AVA_BACKUP_VOICE_ID",
        ],
        "canva": [
            "CIRCA_HAUS_CANVA_CLIENT_ID",
            "CIRCA_HAUS_CANVA_CLIENT_SECRET",
            "CIRCA_HAUS_CANVA_WEBHOOK_SECRET",
        ],
        "apliiq": [
            "CIRCA_HAUS_APLIIQ_API_KEY",
            "CIRCA_HAUS_APLIIQ_API_SECRET",
            "CIRCA_HAUS_APLIIQ_WEBHOOK_SECRET",
        ],
        "printful": [
            "CIRCA_HAUS_PRINTFUL_API_TOKEN",
            "CIRCA_HAUS_PRINTFUL_WEBHOOK_SECRET",
        ],
        "cloudflare": [
            "CIRCA_HAUS_CLOUDFLARE_ACCOUNT_ID",
            "CIRCA_HAUS_CLOUDFLARE_ZONE_ID",
            "CIRCA_HAUS_CLOUDFLARE_API_TOKEN",
            "CIRCA_HAUS_PUBLIC_APP_DOMAIN",
            "CIRCA_HAUS_ADMIN_DOMAIN",
            "CIRCA_HAUS_QR_DOMAIN",
        ],
        "google_workspace": [
            "CIRCA_HAUS_SUPPORT_EMAIL",
            "CIRCA_HAUS_ADMIN_EMAIL",
            "CIRCA_HAUS_GOOGLE_WORKSPACE_DOMAIN",
        ],
        "amazon_ses": [
            "CIRCA_HAUS_SES_REGION",
            "CIRCA_HAUS_SES_ACCESS_KEY_ID",
            "CIRCA_HAUS_SES_SECRET_ACCESS_KEY",
            "CIRCA_HAUS_SES_FROM_EMAIL",
        ],
        "twilio": [
            "CIRCA_HAUS_TWILIO_ACCOUNT_SID",
            "CIRCA_HAUS_TWILIO_MESSAGING_SERVICE_SID",
            "CIRCA_HAUS_TWILIO_AUTH_TOKEN",
            "CIRCA_HAUS_TWILIO_WEBHOOK_SECRET",
        ],
        "epidemic_sound": [
            "CIRCA_HAUS_EPIDEMIC_SOUND_CLIENT_ID",
            "CIRCA_HAUS_EPIDEMIC_SOUND_CLIENT_SECRET",
            "CIRCA_HAUS_EPIDEMIC_SOUND_WEBHOOK_SECRET",
        ],
        "artlist": [
            "CIRCA_HAUS_ARTLIST_CLIENT_ID",
            "CIRCA_HAUS_ARTLIST_CLIENT_SECRET",
            "CIRCA_HAUS_ARTLIST_WEBHOOK_SECRET",
        ],
    },
    "exclusivity": {
        "supabase": [
            "EXCLUSIVITY_SUPABASE_URL",
            "EXCLUSIVITY_SUPABASE_SERVICE_ROLE_KEY",
            "EXCLUSIVITY_ETHER_SIGNAL_SECRET",
        ],
        "stripe": ["EXCLUSIVITY_STRIPE_SECRET_KEY"],
        "twilio": ["EXCLUSIVITY_TWILIO_ACCOUNT_SID"],
        "openai": ["EXCLUSIVITY_OPENAI_API_KEY"],
        "elevenlabs": ["EXCLUSIVITY_ELEVENLABS_API_KEY"],
    },
}


def _has_env(key: str) -> bool:
    return bool(os.getenv(key, "").strip())


def _required_set(project_slug: str) -> set[str]:
    slug = project_slug.strip().lower()
    if slug == "circa_haus":
        return set(CIRCA_HAUS_LAUNCH_REQUIRED)
    if slug == "exclusivity":
        return set(EXCLUSIVITY_LAUNCH_REQUIRED)
    return {"supabase"}


def _conditional_set(project_slug: str) -> set[str]:
    slug = project_slug.strip().lower()
    if slug == "circa_haus":
        return set(CIRCA_HAUS_CONDITIONAL_PROVIDERS)
    return set()


def _signature_required_set(project_slug: str) -> set[str]:
    slug = project_slug.strip().lower()
    if slug == "circa_haus":
        return set(CIRCA_HAUS_SIGNATURE_REQUIRED)
    if slug == "exclusivity":
        return set(EXCLUSIVITY_SIGNATURE_REQUIRED)
    return set()


def provider_readiness_for_project(project_slug: str) -> Dict[str, Any]:
    project = get_project(project_slug)
    if project is None:
        return {
            "ok": False,
            "error": {
                "code": "ETHER_PROJECT_NOT_FOUND",
                "message": "Project could not be resolved for provider readiness.",
                "project_slug": project_slug,
            },
        }

    required = _required_set(project.slug)
    conditional = _conditional_set(project.slug)
    signature_required = _signature_required_set(project.slug)
    tracked_providers = set(project.provider_set.keys()).union(required).union(conditional)
    signature_readiness = signature_readiness_for_project(project.slug, sorted(tracked_providers))
    signature_by_provider = {
        row.get("provider"): row for row in signature_readiness.get("providers", [])
    }
    provider_rows: List[Dict[str, Any]] = []
    launch_blockers: List[str] = []
    env_requirements = PROVIDER_ENV_REQUIREMENTS.get(project.slug, {})

    for provider in sorted(tracked_providers):
        enabled = bool(project.provider_set.get(provider, provider in required or provider in conditional))
        normalized = provider.strip().lower()
        disabled = control_plane_state.provider_disabled(project.slug, normalized)
        required_for_launch = normalized in required
        conditional_provider = normalized in conditional
        signature_required_for_launch = normalized in signature_required
        signature_configured = bool(signature_by_provider.get(normalized, {}).get("configured"))
        needed = env_requirements.get(normalized, [])
        configured = True
        notes: List[str] = []

        if normalized == "supabase":
            signal = project_signal_readiness(project.slug).to_dict()
            configured = bool(signal.get("ready_for_real_signal")) and all(_has_env(key) for key in needed)
            missing = [key for key in needed if not _has_env(key)]
            if missing:
                notes.extend([f"Missing {key}."] for key in missing)
            notes.extend(signal.get("notes") or [])
        elif needed:
            missing = [key for key in needed if not _has_env(key)]
            configured = not missing
            if missing:
                notes.extend([f"Missing {key}." for key in missing])
            else:
                notes.append("Required environment variables are present.")
        else:
            configured = bool(enabled)
            notes.append("No explicit environment requirements are registered for this provider yet.")

        if conditional_provider:
            notes.append(
                "Conditional provider: track readiness, but do not block launch until official API/partner access, licensing scope, cost, and usage-right verification are confirmed."
            )

        signature_row = signature_by_provider.get(normalized)
        if signature_row and signature_row.get("supported"):
            if signature_configured:
                notes.append("Provider webhook signature verification secret is configured.")
            else:
                notes.append("Provider webhook signature verification secret is not configured.")
        if signature_required_for_launch and not signature_configured:
            notes.append("Provider webhook signature verification is required before live launch trust.")

        if disabled:
            notes.append("Provider is disabled by Ether control plane.")
        if not enabled:
            notes.append("Provider is not enabled for this project registry.")

        launch_blocking = bool(
            enabled
            and not conditional_provider
            and (
                (required_for_launch and (disabled or not configured))
                or (signature_required_for_launch and not signature_configured)
            )
        )
        if launch_blocking:
            launch_blockers.append(normalized)

        provider_rows.append(
            ProviderReadinessResult(
                provider=normalized,
                enabled=bool(enabled),
                disabled_by_control_plane=disabled,
                configured=configured,
                signature_configured=signature_configured,
                signature_required_for_launch=signature_required_for_launch,
                required_for_launch=required_for_launch,
                launch_blocking=launch_blocking,
                notes=notes,
            ).to_dict()
        )

    project_disabled = control_plane_state.project_disabled(project.slug)
    if project_disabled:
        launch_blockers.append("project_disabled")

    unique_launch_blockers = sorted(set(launch_blockers))

    return {
        "ok": True,
        "project_slug": project.slug,
        "display_name": project.display_name,
        "project_disabled": project_disabled,
        "launch_ready": not unique_launch_blockers,
        "launch_blockers": unique_launch_blockers,
        "required_providers": sorted(required),
        "conditional_providers": sorted(conditional),
        "signature_required_providers": sorted(signature_required),
        "signature_readiness": signature_readiness,
        "providers": provider_rows,
    }


def provider_readiness_for_suite() -> Dict[str, Any]:
    projects = [provider_readiness_for_project(project.slug) for project in list_projects()]
    launch_blockers = {
        row.get("project_slug", "unknown"): row.get("launch_blockers", [])
        for row in projects
        if row.get("launch_blockers")
    }
    core = [row for row in projects if row.get("project_slug") in {"circa_haus", "exclusivity"}]
    return {
        "ok": True,
        "suite_launch_ready": not launch_blockers and all(row.get("launch_ready") for row in core),
        "launch_blockers": launch_blockers,
        "core_projects": ["circa_haus", "exclusivity"],
        "projects": projects,
    }
