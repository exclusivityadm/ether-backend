from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from app.utils.control_plane import control_plane_state
from app.utils.project_supabase_signal import project_signal_readiness
from app.utils.projects import get_project, list_projects


@dataclass(frozen=True)
class ProviderReadinessResult:
    provider: str
    enabled: bool
    disabled_by_control_plane: bool
    configured: bool
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
}

EXCLUSIVITY_LAUNCH_REQUIRED = {
    "supabase",
}

PROVIDER_ENV_REQUIREMENTS: Dict[str, Dict[str, List[str]]] = {
    "circa_haus": {
        "supabase": ["CIRCA_HAUS_SUPABASE_URL", "CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY"],
        "stripe": ["CIRCA_HAUS_STRIPE_SECRET_KEY", "CIRCA_HAUS_STRIPE_WEBHOOK_SECRET"],
        "openai": ["CIRCA_HAUS_OPENAI_API_KEY"],
        "elevenlabs": ["CIRCA_HAUS_ELEVENLABS_API_KEY", "CIRCA_HAUS_ELEVENLABS_TALETHIA_VOICE_ID"],
        "canva": ["CIRCA_HAUS_CANVA_CLIENT_ID", "CIRCA_HAUS_CANVA_CLIENT_SECRET"],
        "apliiq": ["CIRCA_HAUS_APLIIQ_API_KEY"],
        "printful": ["CIRCA_HAUS_PRINTFUL_API_TOKEN"],
        "cloudflare": ["CIRCA_HAUS_CLOUDFLARE_ZONE_ID"],
        "google_workspace": ["CIRCA_HAUS_SUPPORT_EMAIL", "CIRCA_HAUS_ADMIN_EMAIL"],
        "amazon_ses": ["CIRCA_HAUS_SES_FROM_EMAIL"],
        "twilio": ["CIRCA_HAUS_TWILIO_ACCOUNT_SID", "CIRCA_HAUS_TWILIO_MESSAGING_SERVICE_SID"],
    },
    "exclusivity": {
        "supabase": ["EXCLUSIVITY_SUPABASE_URL", "EXCLUSIVITY_SUPABASE_SERVICE_ROLE_KEY"],
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
    provider_rows: List[Dict[str, Any]] = []
    launch_blockers: List[str] = []
    env_requirements = PROVIDER_ENV_REQUIREMENTS.get(project.slug, {})

    for provider, enabled in sorted(project.provider_set.items()):
        normalized = provider.strip().lower()
        disabled = control_plane_state.provider_disabled(project.slug, normalized)
        required_for_launch = normalized in required
        needed = env_requirements.get(normalized, [])
        configured = True
        notes: List[str] = []

        if normalized == "supabase":
            signal = project_signal_readiness(project.slug).to_dict()
            configured = bool(signal.get("ready_for_real_signal"))
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

        if disabled:
            notes.append("Provider is disabled by Ether control plane.")
        if not enabled:
            notes.append("Provider is not enabled for this project registry.")

        launch_blocking = bool(enabled and required_for_launch and (disabled or not configured))
        if launch_blocking:
            launch_blockers.append(normalized)

        provider_rows.append(
            ProviderReadinessResult(
                provider=normalized,
                enabled=bool(enabled),
                disabled_by_control_plane=disabled,
                configured=configured,
                required_for_launch=required_for_launch,
                launch_blocking=launch_blocking,
                notes=notes,
            ).to_dict()
        )

    project_disabled = control_plane_state.project_disabled(project.slug)
    if project_disabled:
        launch_blockers.append("project_disabled")

    return {
        "ok": True,
        "project_slug": project.slug,
        "display_name": project.display_name,
        "project_disabled": project_disabled,
        "launch_ready": not launch_blockers,
        "launch_blockers": launch_blockers,
        "required_providers": sorted(required),
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
