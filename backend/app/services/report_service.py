"""Groq LLM Grounded Report Synthesis Service Module.

Extracted from:
notebooks/OSCC_Integrated_GraphRAG_EfficientNet_XAI_FINAL_FIXED.ipynb (Cells 6, 8)

Responsibilities:
- Initialize Groq API client using settings.GROQ_API_KEY.
- Bound and sanitize prompt inputs to prevent context window overflow (max 60,000 chars).
- Format structured JSON prompt containing model predictions, XAI summaries, and retrieved evidence.
- Send chat completion request to Groq LLM enforcing exact temperature (0.2) and token limits (4096).
- Strict evidence-grounding instructions and clinical disclaimers (7 mandatory sections).
- Graceful degradation: return structured error dictionary on API failure without failing endpoint.
- Security: never expose API keys or sensitive patient data in logs or responses.
"""

from datetime import datetime, timezone
import json
import threading
from typing import Any, Dict, List, Optional
from app.config import settings
from app.core.logging import logger

MAX_REPORT_PROMPT_CHARS: int = 60000
DEFAULT_GROQ_MODEL: str = "llama-3.3-70b-versatile"

# System instruction verbatim from Notebook Cell 8
REPORT_SYSTEM_INSTRUCTION: str = """
You are a research-support assistant for an oral cancer histopathology project.
Use only supplied case data, retrieved graph context and retrieved literature.

Rules:
- The classifier output is a model prediction, not a clinical probability or diagnosis.
- The OSCC sigmoid score is a model score, not probability that a patient has cancer.
- Heatmaps indicate model attribution only; they do not prove a lesion, cancer, or pathology location.
- Never infer histological features or biomarkers from heatmap statistics.
- Graph relationships and literature are research/population context, not case-specific findings.
- Only cite references supplied in retrieved chunks. Exact paper_id matches may be described as shared identifiers; do not invent graph edges.
- Separate retrieved evidence from generated interpretation and disclose missing evidence.
- Never invent patient information, references, or findings. Do not recommend treatment.
- Explicitly state this is research/academic support, not a clinical diagnosis.

Use these sections: Case Summary; Model Prediction; XAI Attribution; Knowledge-Graph Context; Retrieved Literature; Integrated Research Interpretation; Limitations.
"""


def _bound_prompt_value(value: Any, max_string: int = 5000, max_items: int = 40) -> Any:
    """Recursively bound string lengths and list/dict items to prevent context overflow.

    Preserves exact logic from Notebook Cell 8.
    """
    if isinstance(value, str):
        if len(value) > max_string:
            return value[:max_string] + " [truncated for report context size]"
        return value
    if isinstance(value, dict):
        return {str(k): _bound_prompt_value(v, max_string, max_items) for k, v in list(value.items())[:max_items]}
    if isinstance(value, (list, tuple)):
        return [_bound_prompt_value(v, max_string, max_items) for v in list(value)[:max_items]]
    if value is None or isinstance(value, (int, float, bool)):
        return value
    return str(value)


class ReportService:
    """Manages Groq API integration and grounded research report synthesis."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_prompt_chars: int = MAX_REPORT_PROMPT_CHARS,
    ) -> None:
        """Initialize the ReportService with API credentials and target model."""
        self.api_key: str = api_key or settings.GROQ_API_KEY
        self.model: str = model or settings.GROQ_MODEL or DEFAULT_GROQ_MODEL
        self.max_prompt_chars: int = max_prompt_chars
        self.system_instruction: str = REPORT_SYSTEM_INSTRUCTION.strip()

        self._client: Any = None
        self._is_initialized: bool = False
        self._lock: threading.Lock = threading.Lock()

    @property
    def is_configured(self) -> bool:
        """Return True if an API key is present and not a template placeholder."""
        return bool(self.api_key and not self.api_key.startswith("gsk_your_"))

    def initialize(self) -> bool:
        """Initialize Groq API client with API key.

        Preserves client initialization contract from Notebook Cell 6.
        """
        with self._lock:
            if self._is_initialized and self._client is not None:
                return True

            if not self.is_configured:
                logger.info("Groq API key is not configured; report service running in offline fallback mode.")
                self._is_initialized = False
                return False

            try:
                from groq import Groq
            except ImportError as exc:
                logger.warning("groq library is not installed in the active environment. Detail: %s", exc)
                self._is_initialized = False
                return False

            logger.info("Initializing Groq API client (model='%s')...", self.model)
            try:
                self._client = Groq(api_key=self.api_key)
                self._is_initialized = True
                logger.info("Groq client successfully initialized.")
                return True
            except Exception as exc:
                logger.warning("Failed to initialize Groq client: %s", exc)
                self._client = None
                self._is_initialized = False
                return False

    def make_report_error_response(self, case_id: str, exc: Exception) -> Dict[str, Any]:
        """Format standardized structured error payload matching Pydantic GroqReport schema.

        Preserves exact error structure from Notebook Cell 8.
        """
        logger.warning("Groq report generation unavailable for case '%s' (model='%s'): %s", case_id, self.model, exc)
        return {
            "status": "error",
            "provider": "Groq",
            "model": self.model,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "error": {
                "code": type(exc).__name__,
                "message": f"Report generation unavailable: {exc}",
            },
            "text": None,
        }

    def generate_report(
        self,
        case_id: str,
        filename: str,
        patient_context: Dict[str, str],
        prediction_label: str,
        probability: float,
        threshold: float,
        xai_summary: Dict[str, Any],
        user_question: str,
        graph_context: List[Dict[str, Any]],
        retrieval_query: str,
        literature_evidence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Synthesize structured grounded research report using Groq.

        Preserves exact prompt structure, context bounding, temperature, token limits,
        and guardrails from Notebook Cell 8.

        Args:
            case_id: Standardized case identifier string.
            filename: Original image filename.
            patient_context: Normalized clinical dictionary.
            prediction_label: 'OSCC' or 'Normal'.
            probability: Model sigmoid probability.
            threshold: Classification cutoff threshold.
            xai_summary: Attribution statistics and correlation metrics.
            user_question: Research question.
            graph_context: Retrieved Neo4j disease nodes.
            retrieval_query: Semantic query text.
            literature_evidence: Retrieved FAISS literature chunks.

        Returns:
            Dictionary matching GroqReport Pydantic schema.
        """
        if not self._is_initialized:
            initialized = self.initialize()
            if not initialized or self._client is None:
                exc = RuntimeError("Groq API key not configured or service offline")
                return self.make_report_error_response(case_id, exc)

        payload = {
            "case_id": case_id,
            "filename": filename,
            "user_question": user_question,
            "patient_context": patient_context,
            "classifier": {
                "predicted_class": prediction_label,
                "oscc_probability": float(probability),
                "threshold": float(threshold),
            },
            "xai_summary": xai_summary,
            "knowledge_graph_context": graph_context,
            "retrieval_query": retrieval_query,
            "retrieved_literature": literature_evidence,
        }

        payload = _bound_prompt_value(payload)
        prompt = f"""
Prepare a grounded research explanation for this OSCC image case. Separate model output, attribution, retrieved graph/literature evidence, and synthesis. If a source is missing, say so.

Structured source data (no raw image or heatmap arrays):
{json.dumps(payload, indent=2, ensure_ascii=False)}
"""

        prompt_chars = len(self.system_instruction) + len(prompt)
        if prompt_chars > self.max_prompt_chars:
            exc = ValueError(f"Report context is {prompt_chars} characters; limit is {self.max_prompt_chars}.")
            return self.make_report_error_response(case_id, exc)

        try:
            logger.info("Dispatching grounded report request to Groq for case '%s' (prompt_chars=%d)...", case_id, prompt_chars)
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_instruction},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_completion_tokens=4096,
            )

            if not getattr(response, "choices", None):
                raise RuntimeError("Groq returned no completion choices.")

            choice = response.choices[0]
            content = getattr(getattr(choice, "message", None), "content", None)
            if not isinstance(content, str) or not content.strip():
                raise RuntimeError("Groq returned no text content in response message.")

            if getattr(choice, "finish_reason", None) == "length":
                raise RuntimeError("Groq stopped before completing the report (finish_reason=length).")

            logger.info(
                "Groq report generated case_id=%s model=%s prompt_chars=%d finish_reason=%s",
                case_id, self.model, prompt_chars, getattr(choice, "finish_reason", None),
            )

            return {
                "status": "ok",
                "provider": "Groq",
                "model": self.model,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "text": content.strip(),
                "error": None,
            }

        except Exception as exc:
            return self.make_report_error_response(case_id, exc)


# Global singleton instance
report_service = ReportService()
