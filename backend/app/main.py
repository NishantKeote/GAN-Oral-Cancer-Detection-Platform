"""FastAPI Application Entrypoint for OSCC GraphRAG & Grad-CAM Platform.

Configures CORS, application lifespan management, structured logging,
and includes routers for health checks, analysis, and heatmap streaming.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from app.config import PROJECT_ROOT, settings
from app.core.logging import logger
from app.routers import api_router
from app.services import graph_service, rag_service, report_service, vision_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Initializes expensive machine learning models, vector indices,
    and optional database connections once on startup.
    Executes driver cleanup on application shutdown.
    """
    logger.info("Initializing OSCC GraphRAG Backend (Phase 1G: Pipeline Assembled)...")

    # 1. Ensure artifact directory exists for heatmap storage
    settings.ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Artifact directory verified at: %s", settings.ARTIFACT_DIR)

    # 2. Pre-load EfficientNetB0 model (graceful fallback if TF not in active env)
    try:
        vision_service.load_model()
    except Exception as exc:
        logger.warning("VisionService startup initialization deferred or unavailable: %s", exc)

    # 3. Pre-load FAISS index and SentenceTransformer (graceful fallback if not in active env)
    try:
        rag_service.load_resources()
    except Exception as exc:
        logger.warning("RAGService startup initialization deferred or unavailable: %s", exc)

    # 4. Initialize Neo4j graph driver (optional external service)
    try:
        graph_service.connect()
    except Exception as exc:
        logger.warning("Neo4j startup connection deferred or unavailable: %s", exc)

    # 5. Initialize Groq API client (optional external service)
    try:
        report_service.initialize()
    except Exception as exc:
        logger.warning("Groq startup initialization deferred or unavailable: %s", exc)

    logger.info("Active classification threshold: %f", settings.CLASSIFICATION_THRESHOLD)
    logger.info("Configured CORS origins: %s", settings.CORS_ORIGINS)

    yield

    logger.info("Shutting down OSCC GraphRAG Backend...")
    try:
        graph_service.close()
    except Exception as exc:
        logger.warning("Error closing Neo4j driver during shutdown: %s", exc)


# Initialize FastAPI application
app = FastAPI(
    title="OSCC GraphRAG & Grad-CAM Research Backend",
    description=(
        "Explainable AI and Knowledge-Graph-Augmented decision support API "
        "for Oral Squamous Cell Carcinoma histopathology analysis."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
# Supports Vite, React, and public ngrok tunnels
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://.*\.ngrok-free\.dev$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_router)


@app.get("/api", summary="Root Welcome & Metadata Endpoint")
async def api_info():
    """API metadata endpoint providing platform information and documentation links."""
    return {
        "title": "OSCC GraphRAG & Grad-CAM Research Platform API",
        "version": "2.0.0",
        "status": "online",
        "phase": "1G_pipeline_assembled",
        "documentation": "/docs",
        "health_check": "/health",
        "disclaimer": (
            "This software is an investigational research decision-support tool. "
            "It is not a clinically validated diagnostic device and must not replace "
            "professional histopathological evaluation."
        ),
    }


# Frontend SPA distribution directory
dist_dir = PROJECT_ROOT / "frontend" / "dist"
if dist_dir.is_dir():
    # Mount Vite static assets: /assets -> frontend/dist/assets
    assets_dir = dist_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/", summary="Frontend Root", include_in_schema=False)
    async def serve_root():
        """Serve index.html at root."""
        return FileResponse(dist_dir / "index.html")

    @app.get("/{full_path:path}", summary="Frontend SPA Fallback", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Serve frontend static file or fall back to index.html for client-side routing."""
        target = dist_dir / full_path
        if full_path and target.is_file():
            return FileResponse(target)
        return FileResponse(dist_dir / "index.html")
else:
    @app.get("/", summary="Root Welcome & Metadata Endpoint")
    async def root():
        return await api_info()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
