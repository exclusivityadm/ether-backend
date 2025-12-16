# app/db/supabase.py
from __future__ import annotations

import os
from supabase import create_client, Client

_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """
    Singleton Supabase client for Ether.
    Internal-only. No ORM. No SQLAlchemy.
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        raise RuntimeError("Supabase environment variables not configured")

    _supabase_client = create_client(supabase_url, supabase_key)
    return _supabase_client
