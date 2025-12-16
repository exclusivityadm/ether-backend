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
    version="2.0.1",
    description="Stable Ether API with Supabase + Keepalive uptime"
)

# ---------------------------------------------------------
# Middleware
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Routers
# ---------------------------------------------------------
app.include_router(health_router)
app.include_router(db_status_router)
app.include_router(db_test_router)

# Ether authoritative ingress (internal-only)
app.include_router(ether_ingest_router)

# ---------------------------------------------------------
# Root
# ---------------------------------------------------------
@app.get("/")
async def root():
    return {
        "status": "Ether Backend v2 Online",
        "routes": [
            "/health",
            "/db/status",
            "/db/tables",
            "/db/write",
            "/ether/ingest"
        ]
    }

# ---------------------------------------------------------
# Startup
# ---------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    log.info("Ether v2 starting — keepalive tasks online")
    start_keepalive_tasks()
