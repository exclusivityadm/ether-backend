# app/main.py

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.health import router as health_router
from app.routers.db_status import router as db_router
from app.routers.db_test import router as db_test_router
from app.utils.keepalive import start_keepalive_tasks

log = logging.getLogger("ether_v2.main")

app = FastAPI(
    title="Ether Backend v2",
    version="2.0.0",
    description="Stable Ether API with Supabase connectivity + keepalives"
)


# ----------------------------------------
# CORS (allow dev + production)
# ----------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------
# ROUTES
# ----------------------------------------
app.include_router(health_router)
app.include_router(db_router)        # Supabase health check
app.include_router(db_test_router)   # NEW: Real DB read/write testing


# ----------------------------------------
# STARTUP EVENTS
# ----------------------------------------
@app.on_event("startup")
async def startup_event():
    log.info("Ether v2 backend startup: bootstrapping keepalive tasks")
    start_keepalive_tasks()
    log.info("Keepalive scheduler started")


@app.get("/")
async def root():
    return {"status": "Ether v2 online", "routes": ["/health", "/db/status", "/db/tables", "/db/write"]}


