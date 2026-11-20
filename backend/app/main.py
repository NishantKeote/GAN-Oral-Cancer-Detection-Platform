"""FastAPI Application Entrypoint for OSCC GraphRAG & Grad-CAM Platform.

Configures CORS, application lifespan management, structured logging,
and includes routers for health checks, analysis, and heatmap streaming.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.logging import logger
from app.routers import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup initialization of ML models, FAISS vector stores,
    database connections, and graceful shutdown cleanup.
    """
    logger.info("Initializing OSCC GraphRAG Backend (Phase 1A: Foundation)...")

    # Ensure artifact directory exists for heatmap storage
    settings.ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Artifact directory verified at: %s", settings.ARTIFACT_DIR)

    # Note: ML Model, FAISS index, Neo4j, and Groq initialization
    # will be wired into this lifespan block during Phase 1B extraction.
    logger.info("Active classification threshold: %f", settings.CLASSIFICATION_THRESHOLD)
    logger.info("Configured CORS origins: %s", settings.CORS_ORIGINS)

    yield

    logger.info("Shutting down OSCC GraphRAG Backend...")


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
# Supports Vite (localhost:5173) and React (localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_router)


@app.get("/", summary="Root Welcome & Metadata Endpoint")
async def root():
    """Root endpoint providing platform information and documentation links."""
    return {
        "title": "OSCC GraphRAG & Grad-CAM Research Platform API",
        "version": "2.0.0",
        "status": "online",
        "phase": "1A_foundation",
        "documentation": "/docs",
        "health_check": "/health",
        "disclaimer": (
            "This software is an investigational research decision-support tool. "
            "It is not a clinically validated diagnostic device and must not replace "
            "professional histopathological evaluation."
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
