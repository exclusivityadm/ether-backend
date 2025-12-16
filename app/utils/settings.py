# app/utils/settings.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List


def _split_csv(v: str) -> List[str]:
    return [x.strip() for x in v.split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    # Version fingerprinting
    ETHER_VERSION: str = os.getenv("ETHER_VERSION", "2.0.2-sealed")

    # Internal-only auth
    # REQUIRED in production: set this in Render/Vercel-to-Render callers, etc.
    ETHER_INTERNAL_TOKEN: str = os.getenv("ETHER_INTERNAL_TOKEN", "")

    # Optional caller allowlist (enforced when header present). Keep tight.
    # Example: "exclusivity,sova,nirasova_os,admin"
    ETHER_ALLOWED_SOURCES: List[str] = tuple(_split_csv(os.getenv("ETHER_ALLOWED_SOURCES", "exclusivity,admin")))

    # CORS control: "none" (recommended) or "allowlist"
    ETHER_CORS_MODE: str = os.getenv("ETHER_CORS_MODE", "none")
    ETHER_CORS_ALLOW_ORIGINS: List[str] = tuple(_split_csv(os.getenv("ETHER_CORS_ALLOW_ORIGINS", "")))

    # Ingest safety
    ETHER_MAX_BODY_BYTES: int = int(os.getenv("ETHER_MAX_BODY_BYTES", "1048576"))  # 1MB default
    ETHER_INGEST_RPM: int = int(os.getenv("ETHER_INGEST_RPM", "120"))  # per source, best-effort in-memory
    ETHER_REPLAY_TTL_SECONDS: int = int(os.getenv("ETHER_REPLAY_TTL_SECONDS", "600"))  # 10 min idempotency window


settings = Settings()
