"""Health and readiness probe router."""

from fastapi import APIRouter
from app.config import settings
from app.schemas.health import HealthResponse
from app.services.graph_service import graph_service
from app.services.rag_service import rag_service
from app.services.report_service import report_service
from app.services.vision_service import vision_service
from app.services.xai_service import xai_service

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health & Readiness Probe",
)
async def health_check():
    """Health check endpoint reporting live component readiness and model metadata."""
    return {
        "status": "ok",
        "phase": "1G_pipeline_assembled",
        "model": "EfficientNetB0",
        "threshold": settings.CLASSIFICATION_THRESHOLD,
        "xai_methods": xai_service.method_names,
        "services": {
            "cnn_loaded": vision_service.is_loaded,
            "faiss_loaded": rag_service.is_loaded,
            "neo4j_connected": graph_service.is_connected,
            "groq_configured": report_service.is_configured,
        },
        "version": "2.0.0",
    }
