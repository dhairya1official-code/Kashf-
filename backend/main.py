"""
╔══════════════════════════════════════════════════════════════════════╗
║  KASHF — Personal Privacy Auditor Backend                          ║
║  AMD Slingshot 2026 Hackathon                                      ║
║                                                                     ║
║  An Agentic AI-powered OSINT Privacy Dashboard that maps digital   ║
║  footprints, identifies data leaks, and automates privacy          ║
║  takedowns using 100% local AI inference.                          ║
╚══════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from utils.secure_wipe import wipe_expired_tasks

# ── Logging setup ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-28s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("kashf")


# ── Background auto-wipe task ─────────────────────────────────────────
async def _auto_wipe_loop() -> None:
    """Periodically wipe expired scan data for privacy."""
    while True:
        try:
            await wipe_expired_tasks()
        except Exception as exc:
            logger.error(f"Auto-wipe error: {exc}")
        await asyncio.sleep(3600)  # Check every hour


# ── App lifespan ──────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("🛡️  Kashf Privacy Dashboard — Starting up…")
    await init_db()
    logger.info("✅ Database initialized")

    # Launch background auto-wipe task
    wipe_task = asyncio.create_task(_auto_wipe_loop())
    logger.info(f"🧹 Auto-wipe enabled (TTL: {settings.DATA_TTL_HOURS}h)")

    if settings.LLM_MODEL_PATH:
        logger.info(f"🧠 LLM model configured: {settings.LLM_MODEL_PATH}")
    else:
        logger.info("📝 No LLM model configured — using template-based takedown emails")

    logger.info("🚀 Kashf backend ready!")

    yield

    # Shutdown
    wipe_task.cancel()
    logger.info("👋 Kashf backend shutting down")


# ── FastAPI Application ──────────────────────────────────────────────

app = FastAPI(
    title="Kashf — Personal Privacy Auditor",
    description=(
        "OSINT Privacy Dashboard for the AMD Slingshot 2026 Hackathon. "
        "Aggregates digital footprints across 20+ platforms, scores privacy "
        "risks using local AI, and generates GDPR/CCPA takedown emails — "
        "all with 100% data privacy (zero cloud API calls)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register API routers ─────────────────────────────────────────────
from api.search import router as search_router
from api.results import router as results_router
from api.takedown import router as takedown_router

app.include_router(search_router)
app.include_router(results_router)
app.include_router(takedown_router)


# ── Health check ──────────────────────────────────────────────────────


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": "Kashf Privacy Dashboard",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "search": "POST /search",
            "results": "GET /results/{task_id}",
            "takedown": "POST /takedown",
            "docs": "GET /docs",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "llm_configured": bool(settings.LLM_MODEL_PATH),
        "hibp_configured": bool(settings.HIBP_API_KEY),
        "shodan_configured": bool(settings.SHODAN_API_KEY),
        "data_ttl_hours": settings.DATA_TTL_HOURS,
    }
