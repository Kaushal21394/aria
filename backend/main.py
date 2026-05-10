from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.database import init_db
from .routers import brief, research
from .routers import auth_router, admin, chat

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")

app = FastAPI(
    title="ARIA — Account Research & Intelligence Agent",
    description=(
        "Phase 4: Production SaaS — JWT auth, multi-tenancy, "
        "usage metering, rate limiting, MCP integration."
    ),
    version="4.0.0",
)

# Initialise SQLite usage DB on startup (creates tables + seeds demo orgs)
@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routes (no auth)
app.include_router(auth_router.router)

# Protected routes (require JWT or API key)
app.include_router(brief.router)
app.include_router(research.router)
app.include_router(admin.router)
app.include_router(chat.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ARIA", "version": "4.0.0"}
