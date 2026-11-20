"""Analysis Orchestration Service Module.

Extracted from:
notebooks/OSCC_Integrated_GraphRAG_EfficientNet_XAI_FINAL_FIXED.ipynb (Cells 7, 8, 9)

Responsibilities:
- Orchestrates the complete multimodal oral cancer decision-support pipeline.
- Coordinates the 5 domain services in dependency order:
    1. VisionService: Image decode, 224x224 scaling, and EfficientNetB0 forward scoring.
    2. XAIService: 4-method gradient attribution generation, overlay blending, and PNG persistence.
    3. RAGService: Dynamic query assembly, MiniLM encoding, and FAISS top-k literature retrieval.
    4. GraphService: Parameterized Neo4j disease relationship traversal and case persistence.
    5. ReportService: Grounded Groq research report synthesis with context bounding and disclaimers.
- Robust error recovery: graceful degradation when optional external services (Neo4j, Groq)
  are offline or unconfigured, returning partial 200 OK responses with structured error logs.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid
from app.config import settings
from app.core.logging import logger
from app.services.graph_service import graph_service
from app.services.rag_service import rag_service
from app.services.report_service import report_service
from app.services.vision_service import vision_service
from app.services.xai_service import xai_service


class AnalysisService:
    """Orchestrates end-to-end multimodal case analysis."""

    def __init__(
        self,
        vision_svc=vision_service,
        xai_svc=xai_service,
        rag_svc=rag_service,
        graph_svc=graph_service,
        report_svc=report_service,
    ) -> None:
        """Initialize the orchestrator with references to all five domain services."""
        self.vision = vision_svc
        self.xai = xai_svc
        self.rag = rag_svc
        self.graph = graph_svc
        self.report = report_svc

    async def analyze_case(
        self,
        image_bytes: bytes,
        filename: str,
        patient_context: Dict[str, str],
        research_question: str = "",
    ) -> Dict[str, Any]:
        """Execute the complete end-to-end oral cancer analysis pipeline.

        Preserves exact orchestration logic and graceful degradation from Notebook Cell 9:
        1. Predict image class and continuous probability via EfficientNetB0.
        2. Generate 4 XAI heatmaps/overlays and save PNGs under ARTIFACT_DIR/case_id.
        3. Assemble dynamic retrieval query.
        4. Query Neo4j for connected disease context (graceful fallback on failure).
        5. Retrieve FAISS literature chunks and link to graph nodes by paper_id.
        6. Persist case and prediction nodes to Neo4j (graceful fallback on failure).
        7. Synthesize grounded Groq report (graceful fallback on failure).
        8. Return structured payload matching AnalysisResponse schema.

        Args:
            image_bytes: Raw binary bytes of uploaded histopathology image.
            filename: Original uploaded image filename.
            patient_context: Normalized clinical dictionary.
            research_question: Optional guiding research question.

        Returns:
            Dictionary matching Pydantic AnalysisResponse schema.
        """
        if not image_bytes:
            raise ValueError("Uploaded image bytes are empty.")
        if len(image_bytes) > settings.MAX_UPLOAD_BYTES:
            raise ValueError(f"Image size exceeds {settings.MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.")

        # 1. Generate unique case identifier
        case_id: str = "CASE-" + uuid.uuid4().hex[:10].upper()
        clean_filename: str = Path(filename or "uploaded_image").name

        logger.info("Initiating analysis for case '%s' (file='%s')...", case_id, clean_filename)

        # 2. Run EfficientNetB0 inference
        prediction_result = self.vision.predict(image_bytes)
        probability: float = prediction_result["oscc_probability"]
        prediction_label: str = prediction_result["prediction"]
        confidence: float = prediction_result["confidence"]
        image_tensor = prediction_result["image_tensor"]
        rgb_image = prediction_result["rgb_image"]

        # 3. Generate 4-method Explainable AI attributions and save PNG artifacts
        xai_summary = self.xai.generate_attributions(
            image_tensor=image_tensor,
            rgb_image=rgb_image,
            case_id=case_id,
            expected_probability=probability,
        )

        # 4. Assemble dynamic query string
        clean_question: str = research_question.strip() if research_question else ""
        retrieval_query: str = self.rag.build_case_query(
            prediction_label=prediction_label,
            oscc_probability=probability,
            patient_context=patient_context,
            user_question=clean_question,
            xai_summary=xai_summary,
        )

        errors: List[Dict[str, Any]] = []

        # 5. Neo4j Knowledge Graph Context Retrieval (Graceful Fallback)
        try:
            graph_context = self.graph.get_disease_context(retrieval_query)
        except Exception as exc:
            logger.warning("Graph retrieval stage failed for case '%s': %s", case_id, exc)
            graph_context = []
            errors.append({"stage": "graph_retrieval", "error": type(exc).__name__})

        # 6. FAISS Literature Vector Retrieval & Graph Linking (Graceful Fallback)
        try:
            literature_evidence = self.rag.retrieve_literature(retrieval_query, top_k=5)
            literature_evidence = self.rag.connect_literature_to_graph(literature_evidence, graph_context)
        except Exception as exc:
            logger.warning("Literature retrieval stage failed for case '%s': %s", case_id, exc)
            literature_evidence = []
            errors.append({"stage": "literature_retrieval", "error": type(exc).__name__})

        # 7. Neo4j Case Graph Persistence (Graceful Fallback)
        try:
            graph_saved = self.graph.save_case(
                case_id=case_id,
                filename=clean_filename,
                patient_context=patient_context,
                prediction_label=prediction_label,
                probability=probability,
                xai_summary=xai_summary,
                user_question=clean_question,
            )
        except Exception as exc:
            logger.warning("Case graph write stage failed for case '%s': %s", case_id, exc)
            graph_saved = False
            errors.append({"stage": "case_graph_write", "error": type(exc).__name__})

        # 8. Groq Grounded Report Generation (Graceful Fallback)
        try:
            report = self.report.generate_report(
                case_id=case_id,
                filename=clean_filename,
                patient_context=patient_context,
                prediction_label=prediction_label,
                probability=probability,
                threshold=self.vision.threshold,
                xai_summary=xai_summary,
                user_question=clean_question,
                graph_context=graph_context,
                retrieval_query=retrieval_query,
                literature_evidence=literature_evidence,
            )
            if report.get("status") == "error":
                err_code = report.get("error", {}).get("code", "ReportError")
                errors.append({"stage": "report_generation", "error": err_code})
        except Exception as exc:
            logger.warning("Report generation stage failed for case '%s': %s", case_id, exc)
            report = self.report.make_report_error_response(case_id, exc)
            errors.append({"stage": "report_generation", "error": type(exc).__name__})

        logger.info(
            "Analysis complete for case '%s': verdict=%s, confidence=%.2f%%, errors=%d",
            case_id,
            prediction_label,
            confidence * 100.0,
            len(errors),
        )

        # 9. Assemble unified payload matching AnalysisResponse schema
        return {
            "case_id": case_id,
            "filename": clean_filename,
            "patient_context": patient_context,
            "research_question": clean_question,
            "prediction": prediction_label,
            "class_index": int(self.vision.class_mapping[prediction_label]),
            "oscc_probability": float(probability),
            "threshold": float(self.vision.threshold),
            "decision_rule": f"OSCC when OSCC sigmoid score >= {self.vision.threshold:.6f}; otherwise Normal",
            "confidence": float(confidence),
            "confidence_percent": round(confidence * 100.0, 2),
            "xai": xai_summary,
            "graph_saved": bool(graph_saved),
            "graph_context": graph_context,
            "retrieval_query": retrieval_query,
            "literature_evidence": literature_evidence,
            "errors": errors,
            "scope_note": (
                "The model score is not clinical probability. Heatmaps indicate model attribution only "
                "and do not prove pathology. Graph and literature provide research context, not specimen-specific confirmation."
            ),
            "report": report,
        }


# Global singleton instance
analysis_service = AnalysisService()
