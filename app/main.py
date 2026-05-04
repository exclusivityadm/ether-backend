# app/main.py
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.errors import install_error_handlers
from app.middleware.internal_gate import InternalOnlyGate

from app.routers.auth import router as auth_router
from app.routers.controls import router as controls_router
from app.routers.health import router as health_router
from app.routers.version import router as version_router
from app.routers.ether_ingest import router as ether_ingest_router
from app.routers.db_status import router as db_status_router
from app.routers.db_test import router as db_test_router
from app.routers.operations import router as operations_router
from app.routers.phantom_core import router as phantom_core_router
from app.routers.projects import router as projects_router
from app.routers.providers import router as providers_router
from app.routers.readiness import router as readiness_router
from app.routers.sentinel import router as sentinel_router
from app.routers.signal import router as signal_router
from app.routers.webhooks import router as webhooks_router

from app.utils.audit import initialize_audit
from app.utils.control_plane import control_plane_state
from app.utils.phantom_core import phantom_core
from app.utils.phantom_keepalive import phantom_keepalive_lane
from app.utils.sentinel import sentinel_engine
from app.utils.settings import settings
from app.utils.signal_verification_store import init_signal_verification_store
from app.utils.webhook_store import init_webhook_store

log = logging.getLogger("ether_v2.main")

app = FastAPI(
    title="Ether Backend v2",
    version=settings.ETHER_VERSION,
    description="Sealed internal-only Ether API with provider resilience, operations, Sentinel, signal lanes, and always-on Phantom Core sovereignty containment.",
)

install_error_handlers(app)

if settings.ETHER_CORS_MODE == "allowlist":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ETHER_CORS_ALLOW_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"]
    )

app.add_middleware(
    InternalOnlyGate,
    internal_token=settings.ETHER_INTERNAL_TOKEN,
    allowed_sources=settings.ETHER_ALLOWED_SOURCES,
    exempt_prefixes=("/health", "/version", "/"),
)

app.include_router(health_router)
app.include_router(version_router)
app.include_router(ether_ingest_router)
app.include_router(db_status_router)
app.include_router(db_test_router)
app.include_router(projects_router)
app.include_router(readiness_router)
app.include_router(operations_router)
app.include_router(auth_router)
app.include_router(controls_router)
app.include_router(providers_router)
app.include_router(webhooks_router)
app.include_router(sentinel_router)
app.include_router(signal_router)
app.include_router(phantom_core_router)

@app.get("/")
async def root():
    return {
        "status": "Ether Backend v2 Online (SEALED)",
        "mode": "internal-only",
        "routes": [
            "/health",
            "/health/deep",
            "/version",
            "/ether/ingest",
            "/projects",
            "/projects/bootstrap",
            "/readiness",
            "/readiness/{project_slug}",
            "/operations/production/gate",
            "/operations/production/checklist",
            "/operations/suite/status",
            "/operations/suite/smoke",
            "/operations/cron/status",
            "/operations/cron/signal",
            "/operations/audit/recent",
            "/operations/audit/summary",
            "/operations/signal/health",
            "/operations/signal/history",
            "/operations/signal/readiness",
            "/operations/signal/all",
            "/operations/signal/{project_slug}",
            "/auth/verify",
            "/controls",
            "/controls/summary",
            "/controls/blockers",
            "/controls/history",
            "/controls/impact/{project_slug}",
            "/controls/recovery/{project_slug}",
            "/controls/recover",
            "/controls/project/disable",
            "/controls/project/enable",
            "/controls/provider/disable",
            "/controls/provider/enable",
            "/providers/{project_slug}",
            "/providers/{project_slug}/readiness",
            "/providers/readiness/suite",
            "/webhooks/status",
            "/webhooks/events",
            "/webhooks/{provider}/{project_slug}",
            "/sentinel/status",
            "/sentinel/enforce",
            "/sentinel/recovery/{project_slug}",
            "/sentinel/recovery",
            "/sentinel/events",
            "/sentinel/review",
            "/sentinel/review/manual",
            "/sentinel/quarantine",
            "/sentinel/quarantine/release",
            "/sentinel/quarantines",
            "/signal/handshake",
            "/signal/heartbeat",
            "/signal/lanes",
            "/phantom/status",
            "/phantom/health",
            "/phantom/gate",
            "/phantom/containment",
            "/phantom/recovery",
            "/phantom/events",
            "/phantom/invariants",
            "/phantom/keepalive/status",
            "/phantom/keepalive/run",
            "/phantom/keepalive/configure",
            "/db/status",
            "/db/tables",
            "/db/write",
        ],
    }

@app.on_event("startup")
async def startup_event():
    initialize_audit()
    control_plane_state.initialize()
    sentinel_engine.initialize()
    phantom_core.initialize()
    init_webhook_store()
    init_signal_verification_store()
    asyncio.create_task(phantom_keepalive_lane.start_background_loop())
    log.info("Ether v2 starting — persistent audit, admin controls, Sentinel, provider webhook operations, verified signals, production gate, readiness, operations, Phantom Core, and Phantom keepalive loaded")
