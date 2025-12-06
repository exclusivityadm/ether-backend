import logging
import os
from functools import lru_cache

from supabase import create_client, Client

logger = logging.getLogger("ether_v2.supabase")


class SupabaseNotConfigured(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_ANON_KEY", "").strip()

    if not url or not key:
        raise SupabaseNotConfigured("SUPABASE_URL or SUPABASE_ANON_KEY not set")

    logger.info("Creating Supabase client for %s", url)
    return create_client(url, key)
