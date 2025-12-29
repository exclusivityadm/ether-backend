# app/main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.errors import install_error_handlers
from app.middleware.internal_gate import InternalOnlyGate

from app.routers.health import router as health_router
from app.routers.version import router as version_router
from app.routers.ether_ingest import router as ether_ingest_router
from app.routers.db_status import router as db_status_router
from app.routers.db_test import router as db_test_router

from app.utils.settings import settings

log = logging.getLogger("ether_v2.main")

app = FastAPI(
    title="Ether Backend v2",
    version=settings.ETHER_VERSION,
    description="Sealed internal-only Ether API (contracts + ingest + observability)",
)

# ---- Errors first: stable envelopes, no trace leaks ----
install_error_handlers(app)

# ---- CORS: locked down (or disabled) ----
if settings.ETHER_CORS_MODE == "allowlist":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ETHER_CORS_ALLOW_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

# ---- Internal-only gate ----
app.add_middleware(
    InternalOnlyGate,
    internal_token=settings.ETHER_INTERNAL_TOKEN,
    allowed_sources=settings.ETHER_ALLOWED_SOURCES,
    exempt_prefixes=("/health", "/version", "/"),
)

# ---- Routers ----
app.include_router(health_router)
app.include_router(version_router)
app.include_router(ether_ingest_router)
app.include_router(db_status_router)
app.include_router(db_test_router)

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
            "/db/status",
            "/db/tables",
            "/db/write",
        ],
    }

@app.on_event("startup")
async def startup_event():
    log.info("Ether v2 starting — no keepalive tasks loaded")
