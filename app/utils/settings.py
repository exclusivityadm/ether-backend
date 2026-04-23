# app/utils/settings.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional


def _split_csv(v: str) -> List[str]:
    return [x.strip() for x in v.split(",") if x.strip()]


def _clean(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    v = v.strip()
    return v or None


@dataclass(frozen=True)
class Settings:
    # Version fingerprinting
    ETHER_VERSION: str = os.getenv("ETHER_VERSION", "2.1.0-foundation")

    # Internal-only auth
    ETHER_INTERNAL_TOKEN: str = os.getenv("ETHER_INTERNAL_TOKEN", "")

    # Optional caller allowlist (enforced when header present). Keep tight.
    ETHER_ALLOWED_SOURCES: List[str] = tuple(
        _split_csv(os.getenv("ETHER_ALLOWED_SOURCES", "exclusivity,sova,circa_haus,admin"))
    )

    # CORS control: "none" (recommended) or "allowlist"
    ETHER_CORS_MODE: str = os.getenv("ETHER_CORS_MODE", "none")
    ETHER_CORS_ALLOW_ORIGINS: List[str] = tuple(_split_csv(os.getenv("ETHER_CORS_ALLOW_ORIGINS", "")))

    # Ingest safety
    ETHER_MAX_BODY_BYTES: int = int(os.getenv("ETHER_MAX_BODY_BYTES", "1048576"))
    ETHER_INGEST_RPM: int = int(os.getenv("ETHER_INGEST_RPM", "120"))
    ETHER_REPLAY_TTL_SECONDS: int = int(os.getenv("ETHER_REPLAY_TTL_SECONDS", "600"))

    # Control-plane foundation
    ETHER_ENVIRONMENT: str = os.getenv("ETHER_ENVIRONMENT", "development")
    ETHER_PROJECT_REGISTRY_JSON: Optional[str] = _clean(os.getenv("ETHER_PROJECT_REGISTRY_JSON"))
    ETHER_ADMIN_AUDIT_LOG: bool = os.getenv("ETHER_ADMIN_AUDIT_LOG", "true").lower() == "true"

    # Backward-compatible project config expected by existing Ether modules
    ETHER_PROJECTS_JSON: Optional[str] = _clean(
        os.getenv("ETHER_PROJECTS_JSON") or os.getenv("ETHER_PROJECT_REGISTRY_JSON")
    )
    ETHER_BOOTSTRAP_EXPOSE_PUBLIC_CONFIG: bool = (
        os.getenv("ETHER_BOOTSTRAP_EXPOSE_PUBLIC_CONFIG", "false").lower() == "true"
    )


settings = Settings()
