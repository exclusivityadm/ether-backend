# app/utils/keepalive.py
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from app.db.supabase import get_supabase_client

log = logging.getLogger("ether_v2.keepalive")

_KEEPALIVE_TASK: Optional[asyncio.Task] = None
_INTERVAL_SECONDS = 300  # 5 minutes (safe, cheap, effective)


async def _keepalive_loop() -> None:
    """
    Internal Ether keepalive.
    Touches Supabase periodically to prevent service-level idling
    and to keep the event loop warm.
    """
    while True:
        try:
            supabase = get_supabase_client()
            supabase.table("ether_test").select("id").limit(1).execute()
            log.debug("Ether keepalive tick")
        except Exception as exc:
            # Never crash Ether for keepalive issues
            log.warning("Ether keepalive failed: %s", exc)

        await asyncio.sleep(_INTERVAL_SECONDS)


def start_keepalive_tasks() -> None:
    global _KEEPALIVE_TASK

    if _KEEPALIVE_TASK is not None:
        return

    loop = asyncio.get_event_loop()
    _KEEPALIVE_TASK = loop.create_task(_keepalive_loop())
