from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

from app.db import init_db
from app.settings import settings
from app.routers.merchant import router as merchant_router
from app.routers.receipts import router as receipts_router
from app.services.scheduler import start_scheduler

log = logging.getLogger("uvicorn")

app = FastAPI(title="Ether Backend", version="1.0.0")


# -----------------------------------------------------
# CORS
# -----------------------------------------------------
origins_env = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
allow_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
allow_origin_regex = None if allow_origins else r".*"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------
# Startup
# -----------------------------------------------------
@app.on_event("startup")
async def startup_event():
    log.info("Initializing database schema…")
    await init_db()

    log.info("Starting keepalive scheduler…")
    await start_scheduler()


# -----------------------------------------------------
# Health
# -----------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}


# -----------------------------------------------------
# Routers
# -----------------------------------------------------
app.include_router(merchant_router, prefix="/merchant", tags=["merchant"])
app.include_router(receipts_router, prefix="/receipts", tags=["receipts"])
