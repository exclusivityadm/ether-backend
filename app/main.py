# app/main.py

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.health import router as health_router
from app.routers.db_status import router as db_status_router
from app.routers.db_test import router as db_test_router

from app.routes.ether_ingest import router as ether_ingest_router
from app.routes.ether_status import router as ether_status_router

from app.utils.keepalive import start_keepalive_tasks

log = logging.getLogger("ether_v2.main")

app = FastAPI(
    title="Ether Backend v2",
    version="2.0.1",
    description="Authoritative internal Ether API"
)

# ----------------------------
# CORS (internal only, permissive by topology)
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Core routers
# ----------------------------
app.include_router(health_router)
app.include_router(db_status_router)
app.include_router(db_test_router)

# ----------------------------
# Ether authoritative surfaces
# ----------------------------
app.include_router(ether_ingest_router)
app.include_router(ether_status_router)


@app.get("/")
async def root():
    return {
        "status": "Ether Backend v2 Online",
        "mode": "internal-only",
        "contracts": "enforced",
        "routes": [
            "/health",
            "/db/status",
            "/db/tables",
            "/db/write",
            "/ether/ingest",
            "/ether/status",
        ]
    }


@app.on_event("startup")
async def startup_event():
    log.info("Ether v2 starting — contracts enforced, keepalive online")
    start_keepalive_tasks()
