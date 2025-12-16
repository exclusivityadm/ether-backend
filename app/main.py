# app/main.py

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.health import router as health_router
from app.routers.db_status import router as db_status_router
from app.routers.db_test import router as db_test_router

from app.routes.ether_ingest import router as ether_ingest_router
from app.utils.keepalive import start_keepalive_tasks

log = logging.getLogger("ether_v2.main")

app = FastAPI(
    title="Ether Backend v2",
    version="2.1.0",
    description="Internal-only Ether orchestration layer"
)

# ----------------------------------
# CORS (SAFE: Ether is internal-only)
# ----------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ether is not browser-facing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------
# PUBLIC / INTERNAL ROUTES
# ----------------------------------

app.include_router(health_router)
app.include_router(db_status_router)
app.include_router(db_test_router)

# INTERNAL-ONLY ETHER ROUTES
app.include_router(ether_ingest_router)


@app.get("/")
async def root():
    return {
        "status": "Ether Backend v2 Online",
        "mode": "internal-only",
        "routes": [
            "/health",
            "/db/status",
            "/db/tables",
            "/db/write",
            "/ether/ingest (internal only)",
        ],
    }


@app.on_event("startup")
async def startup_event():
    log.info("Ether v2 starting — keepalive tasks online")
    start_keepalive_tasks()
