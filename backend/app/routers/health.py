"""Health and readiness probe router."""

from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/health", summary="System Health & Readiness Probe")
async def health_check():
    """Health check endpoint reporting backend status and resource readiness.

    In Phase 1B, this will actively check loaded ML models, FAISS indices,
    Neo4j database connectivity, and Groq API readiness.
    """
    return {
        "status": "ready_for_service_extraction",
        "phase": "1A_foundation",
        "model": "EfficientNetB0",
        "threshold": settings.CLASSIFICATION_THRESHOLD,
        "xai_methods": ["Grad-CAM", "Grad-CAM++", "LayerCAM", "HiResCAM"],
        "services": {
            "cnn_loaded": False,
            "faiss_loaded": False,
            "neo4j_connected": False,
            "groq_configured": bool(settings.GROQ_API_KEY),
        },
        "version": "2.0.0",
    }
