"""Primary multimodal analysis router.

Extracted from:
notebooks/OSCC_Integrated_GraphRAG_EfficientNet_XAI_FINAL_FIXED.ipynb (Cell 9)

Responsibilities:
- Validates multipart image upload (MIME check, 20 MB ceiling, non-empty).
- Normalizes patient clinical context (age, sex, tobacco, alcohol, site, magnification).
- Invokes AnalysisService orchestration pipeline.
- Returns unified AnalysisResponse payload conforming to Pydantic contracts.
- Strictly guards against leaking stack traces or credentials in HTTP error responses.
"""

from pathlib import Path
from typing import Dict
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from app.config import settings
from app.core.logging import logger
from app.schemas.response import AnalysisResponse
from app.services.analysis_service import analysis_service

router = APIRouter()


def normalize_patient_context(
    age: str = "",
    sex: str = "",
    tobacco: str = "",
    alcohol: str = "",
    lesion_site: str = "",
    magnification: str = "",
) -> Dict[str, str]:
    """Normalize clinical patient metadata, defaulting blank fields to 'Not provided'."""
    return {
        "age": age.strip() or "Not provided",
        "sex": sex.strip() or "Not provided",
        "tobacco": tobacco.strip() or "Not provided",
        "alcohol": alcohol.strip() or "Not provided",
        "lesion_site": lesion_site.strip() or "Not provided",
        "magnification": magnification.strip() or "Not provided",
    }


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Empty image or decoding failure"},
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {"description": "Image exceeds 20 MB limit"},
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {"description": "Upload is not an image"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Pipeline execution error"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Core model checkpoint not found on server"},
    },
    summary="Multimodal Histopathology & Graph-RAG Analysis",
)
async def analyze_case(
    image: UploadFile = File(..., description="Histopathology image tile (JPEG/PNG)"),
    age: str = Form("", description="Patient age"),
    sex: str = Form("", description="Patient biological sex"),
    tobacco: str = Form("", description="Tobacco use history"),
    alcohol: str = Form("", description="Alcohol consumption history"),
    lesion_site: str = Form("", description="Anatomical site of the lesion"),
    magnification: str = Form("", description="Microscope magnification level (e.g. 400x)"),
    research_question: str = Form("", description="Optional contextual question guiding RAG retrieval"),
):
    """Execute end-to-end oral cancer multimodal analysis pipeline:

    1. Image Preprocessing & EfficientNetB0 classification scoring
    2. 4-method Explainable AI attribution (Grad-CAM, Grad-CAM++, LayerCAM, HiResCAM)
    3. Dynamic query generation & FAISS literature retrieval
    4. Neo4j knowledge graph traversal
    5. Neo4j case persistence
    6. Grounded Groq LLM research report generation
    """
    # 1. Read image bytes with size limit guard
    try:
        image_bytes = await image.read(settings.MAX_UPLOAD_BYTES + 1)
    finally:
        await image.close()

    # 2. Validate upload constraints
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image is empty.",
        )

    if len(image_bytes) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds {settings.MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
        )

    if image.content_type and not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload must be an image (JPEG, PNG, etc.).",
        )

    clean_filename = Path(image.filename or "uploaded_image").name
    patient_context = normalize_patient_context(
        age=age,
        sex=sex,
        tobacco=tobacco,
        alcohol=alcohol,
        lesion_site=lesion_site,
        magnification=magnification,
    )

    # 3. Dispatch to analysis orchestration service
    try:
        result = await analysis_service.analyze_case(
            image_bytes=image_bytes,
            filename=clean_filename,
            patient_context=patient_context,
            research_question=research_question,
        )
        return result

    except ValueError as exc:
        logger.warning("Invalid input or decoding failure for '%s': %s", clean_filename, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image could not be decoded or processed: {exc}",
        ) from exc

    except FileNotFoundError as exc:
        logger.error("Required model checkpoint or vector resource missing: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Required machine learning model checkpoint is not available on server.",
        ) from exc

    except RuntimeError as exc:
        logger.exception("Pipeline runtime execution error for '%s': %s", clean_filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline inference error: {exc}",
        ) from exc

    except Exception as exc:
        logger.exception("Unexpected error during case analysis for '%s': %s", clean_filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal analysis pipeline processing error. Check backend server logs.",
        ) from exc
