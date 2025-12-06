import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.health import router as health_router
from app.routers.db_status import router as db_router
from app.utils.keepalive import start_keepalive

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("ether_v2.main")
logger.info("Starting Ether v2 backend initialization")

app = FastAPI(
    title="Ether Backend v2",
    version="2.0.0",
    description="Minimal but stable Ether v2 backend with Supabase + keepalive.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(db_router)

@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Ether v2 backend startup: bootstrapping keepalive tasks")
    try:
        start_keepalive()
        logger.info("Keepalive scheduler started")
    except Exception as exc:
        logger.exception("Failed to start keepalive scheduler: %s", exc)
