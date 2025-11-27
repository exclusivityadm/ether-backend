# app/main.py

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.scheduler import start_scheduler, shutdown_scheduler

# Routers
from app.routers.ai import router as ai_router
from app.routers.embedding import router as embedding_router
from app.routers.crm import router as crm_router
from app.routers.merchant import router as merchant_router
from app.routers.context import router as context_router
from app.routers.receipts import router as receipts_router

log = logging.getLogger("uvicorn")

app = FastAPI(
    title="Ether API",
    version="1.0.0",
)

# ----------------------------------------------------------
# CORS
# ----------------------------------------------------------
origins_env = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
allow_origins = [o.strip() for o in origins_env.split(",") if o.strip()]

# If no explicit allowlist is set, fall back to common dev frontends
allow_origin_regex = None
if not allow_origins:
    # Allow Vercel previews + local dev
    allow_origin_regex = (
        r"^https://.*\.vercel\.app$"
        r"|^http://localhost:3000$"
        r"|^http://127\.0\.0\.1:3000$"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------
# Routers
# ----------------------------------------------------------
app.include_router(ai_router)
app.include_router(embedding_router)
app.include_router(crm_router)
app.include_router(merchant_router)
app.include_router(context_router)
app.include_router(receipts_router)

# ----------------------------------------------------------
# Lifecycle: keepalive scheduler
# ----------------------------------------------------------
@app.on_event("startup")
async def on_startup() -> None:
    """
    Application startup hook.

    Starts the keepalive scheduler so Ether can ping:
    - SUPABASE_KEEPALIVE_URLS
    - RENDER_KEEPALIVE_URLS
    (configured via environment variables).
    """
    try:
        start_scheduler()
        log.info("Startup: keepalive scheduler started.")
    except Exception as exc:  # pragma: no cover - defensive logging
        log.error("Startup: failed to start keepalive scheduler: %r", exc)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Application shutdown hook. Stops the keepalive scheduler cleanly."""
    try:
        shutdown_scheduler()
        log.info("Shutdown: keepalive scheduler stopped.")
    except Exception as exc:  # pragma: no cover - defensive logging
        log.error("Shutdown: failed to stop keepalive scheduler: %r", exc)

# ----------------------------------------------------------
# Meta / health
# ----------------------------------------------------------
@app.get("/", tags=["meta"])
async def root() -> dict:
    """
    Simple root endpoint so Render / external checks
    can see a non-404 response.
    """
    return {
        "status": "ok",
        "service": "ether",
        "message": "Sova / Ether backend is running.",
    }


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Primary health endpoint used by Render / keepalives."""
    return {"status": "ok", "service": "ether"}
