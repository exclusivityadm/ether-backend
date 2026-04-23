from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional, Tuple

from supabase import Client, create_client

from app.utils.projects import ProjectRecord

log = logging.getLogger("ether_v2.supabase_auth")


@lru_cache(maxsize=16)
def _client_for(url: str, anon_key: str) -> Client:
    return create_client(url, anon_key)


def _project_anon_key(project: ProjectRecord) -> Optional[str]:
    env_key = f"{project.slug.strip().upper()}_SUPABASE_ANON_KEY"
    import os

    value = os.getenv(env_key, "").strip()
    return value or None


def verify_project_access_token(project: ProjectRecord, access_token: Optional[str]) -> Tuple[bool, str, Optional[str]]:
    if not access_token:
        return False, "missing_access_token", None

    if not project.supabase_url:
        return False, "pending_project_supabase_url", None

    anon_key = _project_anon_key(project)
    if not anon_key:
        return False, "pending_project_supabase_anon_key", None

    try:
        client = _client_for(project.supabase_url, anon_key)
        response = client.auth.get_user(access_token)
        user = getattr(response, "user", None)
        if user is None and isinstance(response, dict):
            user = response.get("user")
        user_id = getattr(user, "id", None) if user is not None else None
        if user_id is None and isinstance(user, dict):
            user_id = user.get("id")
        if user_id:
            return True, "supabase_verified", str(user_id)
        return False, "supabase_invalid_token", None
    except Exception as exc:
        log.warning("Supabase verification failed for project=%s: %s", project.slug, exc)
        return False, "supabase_verification_error", None
