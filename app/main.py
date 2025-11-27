# app/main.py

import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# If allowlist empty → allow regex for Vercel + local dev
allow_origin_regex = None if allow_origins else r"^https://.*\.vercel\.app$|^http://localhost:3000$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ----------------------------------------------------------
# Routers
# ----------------------------------------------------------
from app.routers.ai import router as ai_router
from app.routers.embedding import router as embedding_router
from app.routers.crm import router as crm_router
from app.routers.merchant import router as merchant_router
from app.routers.context import router as context_router

app.include_router(ai_router)
app.include_router(embedding_router)
app.include_router(crm_router)
app.include_router(merchant_router)
app.include_router(context_router)

# ----------------------------------------------------------
# Health
# ----------------------------------------------------------
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "ether"}
