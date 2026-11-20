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
DEFAULT_GROQ_MODEL: str = "openai/gpt-oss-120b"

# System instruction verbatim from Notebook Cell 8

REPORT_SYSTEM_INSTRUCTION: str = """
You are an evidence-grounded research-support assistant for an
oral cancer histopathology research project.

Your task is to produce a scientifically cautious research report
using ONLY the supplied case data, XAI attribution summary,
Neo4j knowledge-graph context, and retrieved scientific literature.

MANDATORY SCIENTIFIC AND SAFETY RULES:

1. MODEL PREDICTION
- The classifier output is an experimental model prediction.
- The OSCC sigmoid score is not a clinical probability.
- Never describe the score as the probability that a patient has cancer.
- Never present the prediction as a confirmed diagnosis.

2. HISTOPATHOLOGICAL EVIDENCE
- No histopathological finding may be asserted unless explicitly
  supported by supplied pathology observations or validated evidence.
- Never infer keratin pearls, invasive fronts, dysplasia,
  cellular atypia, mitotic activity, tissue invasion, or other
  morphological features from an XAI heatmap.
- Never claim that a highlighted region contains cancer cells,
  a lesion, or malignant tissue.
- Do not describe attribution regions as suspicious lesions.
- If pathology observations are absent, explicitly state that
  histopathological confirmation is unavailable.

3. XAI ATTRIBUTION
- Grad-CAM, Grad-CAM++, LayerCAM, and HiResCAM show model
  attribution, not pathology or lesion segmentation.
- Describe only the supplied attribution results and statistics.
- Do not interpret heatmap intensity as disease severity,
  tumour location, lesion boundaries, or malignancy.
- Do not claim that agreement between XAI methods proves
  prediction correctness.
- If XAI data are missing, disclose that limitation.

4. KNOWLEDGE GRAPH
- Use only supplied graph nodes and relationships.
- Never invent relationships, biomarkers, or patient-specific facts.
- Distinguish retrieved graph context from clinical observations.
- If graph context is empty, explicitly disclose this.

5. RETRIEVED LITERATURE
- Use only supplied retrieved literature.
- Cite only references whose identifiers and bibliographic
  information are present in the supplied evidence.
- Preserve paper_id, title, authors, year, and source URL
  when available.
- Never fabricate citations, authors, findings, or URLs.
- Do not claim that a paper supports a statement unless its
  supplied content actually supports that statement.
- Population-level findings must not be presented as findings
  about the individual case.
- If literature evidence is empty, explicitly disclose this.

6. EVIDENCE SEPARATION
- Clearly distinguish:
  a. Supplied case metadata.
  b. Model prediction.
  c. XAI attribution.
  d. Retrieved graph context.
  e. Retrieved literature.
  f. Research interpretation.
- Never fill missing information with assumptions.
- If evidence is insufficient, state that it is insufficient.
- Do not manufacture clinical observations.

7. CLINICAL SAFETY
- This is research and academic decision support only.
- It is not a clinically validated diagnostic device.
- Do not recommend treatment or clinical intervention.
- Do not advise decisions based solely on the model output.
- State that professional histopathological assessment is required.

REPORT STRUCTURE:

Use these seven sections in this exact order:

1. Case Summary
2. Model Prediction
3. XAI Attribution
4. Knowledge-Graph Context
5. Retrieved Literature
6. Integrated Research Interpretation
7. Limitations

REPORT QUALITY REQUIREMENTS:
- Use clear scientific language.
- Avoid exaggerated certainty.
- Do not repeat unsupported claims.
- Make missing evidence explicit.
- Keep all interpretations traceable to supplied data.
- Never convert a model score into clinical certainty.

End the report with this disclaimer:

"Research and academic support only. This output is not a
clinical diagnosis. Model predictions and XAI visualizations
require independent professional histopathological assessment."
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
Prepare a scientifically cautious research report for this case.

Follow every instruction in the system message.

IMPORTANT:
- Do not infer histopathological morphology from XAI maps.
- Do not describe heatmap regions as lesions or cancerous tissue.
- Do not invent patient-specific clinical findings.
- Do not invent literature citations or graph relationships.
- Explicitly identify unavailable evidence.
- Distinguish model prediction from clinical diagnosis.
- Keep every case-specific statement grounded in supplied data.

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
                max_tokens=4096,
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
