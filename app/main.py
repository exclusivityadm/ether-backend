# app/main.py

import os
import logging
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import text

from app.db import engine as db_engine
from app.routers.ai import router as ai_router
from app.routers.embedding import router as embedding_router
from app.routers.crm import router as crm_router
from app.routers.merchant import router as merchant_router
from app.routers.context import router as context_router

log = logging.getLogger("uvicorn")

# ----------------------------------------------------------
# FastAPI app
# ----------------------------------------------------------

app = FastAPI(
    title="Ether API",
    version="1.0.0",
)

# ----------------------------------------------------------
# CORS
# ----------------------------------------------------------

origins_env = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
allow_origins: List[str] = [o.strip() for o in origins_env.split(",") if o.strip()]

# If explicit CORS origins are not provided, fall back to a safe default:
# - Any *.vercel.app frontend
# - Local dev on http://localhost:3000
allow_origin_regex: Optional[str] = None
if not allow_origins:
    allow_origin_regex = r"^https://.*\.vercel\.app$|^http://localhost:3000$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ----------------------------------------------------------
# Routers
# ----------------------------------------------------------

app.include_router(ai_router)
app.include_router(embedding_router)
app.include_router(crm_router)
app.include_router(merchant_router)
app.include_router(context_router)

# ----------------------------------------------------------
# Keepalive Scheduler (Step 1)
# ----------------------------------------------------------

# Env controls:
#   KEEPALIVE_DB_ENABLED       -> "true"/"false" (default: false)
#   KEEPALIVE_HTTP_URLS        -> comma-separated list of URLs to ping
#   KEEPALIVE_INTERVAL_SECONDS -> interval in seconds (default: 300)

KEEPALIVE_DB_ENABLED = os.getenv("KEEPALIVE_DB_ENABLED", "false").lower() == "true"
KEEPALIVE_INTERVAL_SECONDS = int(os.getenv("KEEPALIVE_INTERVAL_SECONDS", "300"))

_scheduler: Optional[AsyncIOScheduler] = None


def _parse_keepalive_urls() -> List[str]:
    raw = os.getenv("KEEPALIVE_HTTP_URLS", "") or ""
    return [u.strip() for u in raw.split(",") if u.strip()]


def _db_keepalive_job() -> None:
    """Simple SELECT 1 against Supabase to keep it from pausing."""
    if not KEEPALIVE_DB_ENABLED:
        return

    if db_engine is None:
        log.warning("Keepalive: DB engine is None; skipping DB ping.")
        return

    try:
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log.info("Keepalive: DB ping successful.")
    except Exception as exc:
        log.warning("Keepalive: DB ping failed: %s", exc)


async def _http_keepalive_job() -> None:
    """Ping configured HTTP URLs (Render, Vercel frontends, etc.)"""
    urls = _parse_keepalive_urls()
    if not urls:
        return

    timeout = httpx.Timeout(5.0, connect=3.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for url in urls:
            try:
                # GET is safest; most health endpoints support it.
                resp = await client.get(url)
                log.info(
                    "Keepalive: HTTP %s -> %s (%s)",
                    resp.status_code,
                    url,
                    "ok" if resp.is_success else "non-200",
                )
            except Exception as exc:
                log.warning("Keepalive: HTTP ping failed for %s: %s", url, exc)


@app.on_event("startup")
async def on_startup() -> None:
    global _scheduler

    # Only start the scheduler if we actually have work to do.
    have_db_job = KEEPALIVE_DB_ENABLED
    have_http_job = bool(_parse_keepalive_urls())

    if not (have_db_job or have_http_job):
        log.info("Keepalive: no jobs configured; scheduler will not start.")
        return

    _scheduler = AsyncIOScheduler(timezone="UTC")

    if have_db_job:
        _scheduler.add_job(
            _db_keepalive_job,
            "interval",
            seconds=KEEPALIVE_INTERVAL_SECONDS,
            id="db_keepalive",
            max_instances=1,
            coalesce=True,
        )

    if have_http_job:
        _scheduler.add_job(
            _http_keepalive_job,
            "interval",
            seconds=KEEPALIVE_INTERVAL_SECONDS,
            id="http_keepalive",
            max_instances=1,
            coalesce=True,
        )

    _scheduler.start()
    log.info(
        "Keepalive: scheduler started (DB: %s, HTTP: %s, interval: %s seconds).",
        have_db_job,
        have_http_job,
        KEEPALIVE_INTERVAL_SECONDS,
    )


@app.on_event("shutdown")
async def on_shutdown() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        log.info("Keepalive: scheduler shut down.")

# ----------------------------------------------------------
# Health
# ----------------------------------------------------------

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "ether"}
