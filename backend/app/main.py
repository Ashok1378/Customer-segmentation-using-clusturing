"""
main.py - FastAPI application factory with CORS, routers and health endpoint.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_clustering, routes_dataset, routes_prediction, routes_database
from app.config import settings
from app.database import init_db
from app.services.db_service import db_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Application instance ────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="ML-powered customer segmentation using clustering algorithms with relational database persistence",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS middleware ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(routes_dataset.router)
app.include_router(routes_clustering.router)
app.include_router(routes_prediction.router)
app.include_router(routes_database.router)


# ── Startup event ────────────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup() -> None:
    logger.info(
        "🚀 %s v%s is starting up ...",
        settings.APP_NAME,
        settings.VERSION,
    )
    logger.info("CORS origins: %s", settings.CORS_ORIGINS)
    logger.info("Upload dir:  %s", settings.UPLOAD_DIR)
    logger.info("Models dir:  %s", settings.MODELS_DIR)
    logger.info("Outputs dir: %s", settings.OUTPUTS_DIR)

    # Initialize database tables
    init_db()


# ── Shutdown event ───────────────────────────────────────────────────────────
@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("%s is shutting down.", settings.APP_NAME)


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Health"], summary="Health check")
async def health_check() -> dict:
    """Returns the application health status, version, and database connectivity."""
    db_status = db_service.get_status()
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "database": {
            "connected": db_status.get("connected", False),
            "engine": db_status.get("engine", "unknown"),
            "counts": db_status.get("counts", {}),
        },
    }
