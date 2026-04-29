# app/main.py
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
from app.routers.projects import router as projects_router
from app.routers.providers import router as providers_router
from app.routers.readiness import router as readiness_router
from app.routers.sentinel import router as sentinel_router
from app.routers.signal import router as signal_router
from app.routers.webhooks import router as webhooks_router

from app.utils.settings import settings

log = logging.getLogger("ether_v2.main")

app = FastAPI(
    title="Ether Backend v2",
    version=settings.ETHER_VERSION,
    description="Sealed internal-only Ether API (contracts + ingest + observability + control plane foundation + sentinel scaffold + signal lane foundation + readiness checks + operations)",
)

install_error_handlers(app)

if settings.ETHER_CORS_MODE == "allowlist":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ETHER_CORS_ALLOW_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
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
            "/operations/signal/readiness",
            "/operations/signal/{project_slug}",
            "/auth/verify",
            "/controls",
            "/controls/project/disable",
            "/controls/project/enable",
            "/controls/provider/disable",
            "/controls/provider/enable",
            "/providers/{project_slug}",
            "/webhooks/{provider}/{project_slug}",
            "/sentinel/events",
            "/sentinel/review",
            "/sentinel/quarantine",
            "/sentinel/quarantines",
            "/signal/handshake",
            "/signal/heartbeat",
            "/signal/lanes",
            "/db/status",
            "/db/tables",
            "/db/write",
        ],
    }

@app.on_event("startup")
async def startup_event():
    log.info("Ether v2 starting — control-plane foundation, sentinel scaffold, signal lane foundation, readiness checks, and operations loaded")
