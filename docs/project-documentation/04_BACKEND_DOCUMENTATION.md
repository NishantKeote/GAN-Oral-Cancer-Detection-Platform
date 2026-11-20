# 04. Backend Documentation

## 1. Architectural Overview

The backend subsystem is an asynchronous, enterprise-structured RESTful API built on **FastAPI** and **Python 3.11+**. It decouples the original monolithic research notebook into modular domain services with strict separation of concerns, Pydantic data validation, and graceful degradation for external dependencies.

```
backend/
├── app/
│   ├── config.py              # Centralized Pydantic BaseSettings with dynamic path resolution
│   ├── main.py                # FastAPI app initialization, lifespan, CORS, and router registry
│   ├── core/
│   │   ├── logging.py         # Structured logging configuration
│   │   └── security.py        # MIME verification, path sanitization, and security policies
│   ├── routers/
│   │   ├── health.py          # GET /health - Component status and system telemetry
│   │   ├── analyze.py         # POST /analyze - Orchestrated clinical multimodal inference
│   │   └── heatmaps.py        # GET /heatmaps/{case_id}/{filename} - XAI artifact streaming
│   ├── schemas/
│   │   ├── health.py          # Pydantic schemas for health and readiness checks
│   │   ├── analysis.py        # Request & response contracts for multi-modal analysis
│   │   └── patient.py         # Patient metadata and clinical history schemas
│   └── services/
│       ├── vision_service.py  # EfficientNetB0 inference and image preprocessing
│       ├── xai_service.py     # Grad-CAM, Grad-CAM++, LayerCAM, HiResCAM generation
│       ├── rag_service.py     # SentenceTransformer embeddings and FAISS index search
│       ├── graph_service.py   # Neo4j AuraDB graph traversal and case persistence
│       ├── report_service.py  # Groq API medical LLM report generation
│       └── analysis_service.py# End-to-end multi-service pipeline orchestrator
├── requirements.txt           # Python dependency specifications
└── .env.example               # Template environment variables
```

---

## 2. Configuration & Path Resolution (`app/config.py`)

Configuration management is implemented using `pydantic-settings` (`BaseSettings`). It provides strong typing, environment variable overrides, and dynamic dual-directory filesystem path resolution.

### 2.1 Dynamic Path Anchor Logic
To ensure robustness across execution environments (whether started from repository root `d:\...` or within `backend/`), `config.py` anchors relative paths dynamically:

```python
_current_file = Path(__file__).resolve()
_backend_dir = _current_file.parent.parent
_repo_root = _backend_dir.parent

def _resolve_repo_path(relative_str: str) -> Path:
    # Resolves paths relative to repository root with fallback to backend root
    p = Path(relative_str)
    if p.is_absolute():
        return p
    target = _repo_root / p
    if target.exists() or (_repo_root / "models").exists():
        return target
    return _backend_dir / p
```

### 2.2 Environment Variables & Defaults

| Setting Variable | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `API_V1_STR` | `str` | `""` | Base route prefix (empty string for root routing) |
| `PROJECT_NAME` | `str` | `"Oral Cancer Detection API"` | API application name |
| `DEBUG` | `bool` | `False` | Debug logging and exception traceback display |
| `HOST` | `str` | `"0.0.0.0"` | Bound network interface |
| `PORT` | `int` | `8000` | HTTP listening port |
| `CORS_ORIGINS` | `list[str]` | `["http://localhost:5173", "http://localhost:3000"]` | Allowed frontend web origins |
| `MODEL_PATH` | `Path` | `Path("models/best_efficientnetb0.keras")` | Path to trained Keras vision classifier |
| `CLASSIFICATION_THRESHOLD` | `float` | `0.850266` | Empirically calibrated decision boundary |
| `FAISS_INDEX_PATH` | `Path` | `Path("knowledge_base/oscc_literature.faiss")` | Dense literature vector index |
| `FAISS_METADATA_PATH`| `Path` | `Path("knowledge_base/chunk_metadata.json")` | Chunk text and citation metadata store |
| `EMBEDDING_MODEL` | `str` | `"all-MiniLM-L6-v2"` | HuggingFace embedding bi-encoder identifier |
| `NEO4J_URI` | `str` | `""` | Bolt/Neo4j database connection URI |
| `NEO4J_USER` | `str` | `""` | Database username |
| `NEO4J_PASSWORD` | `str` | `""` | Database authentication secret |
| `GROQ_API_KEY` | `str` | `""` | Groq cloud LLM API secret token |
| `GROQ_MODEL` | `str` | `"llama-3.3-70b-versatile"` | High-parameter medical reasoning model |
| `ARTIFACTS_DIR` | `Path` | `Path("artifacts")` | Disk directory for generated XAI PNG files |

---

## 3. Application Lifecycle & Startup Management (`app/main.py`)

Application lifecycle is managed via the modern FastAPI `lifespan` async context manager:
1. **Startup:**
   - Validates existence of model and knowledge-base artifact directories.
   - Logs loaded configuration parameters with sanitized credential masking.
   - Creates `artifacts/` output directory if missing.
2. **Shutdown:**
   - Closes active Neo4j driver connections via `GraphService.close()`.
   - Flushes file streams and clears GPU/CPU memory pools.

---

## 4. Router Specifications

### 4.1 Health & Telemetry Router (`app/routers/health.py`)
- **Route:** `GET /health`
- **Response Schema:** `HealthResponse` (`app/schemas/health.py`)
- **Functionality:** Queries component statuses asynchronously:
  - `status`: Overall health (`"healthy"` or `"degraded"`).
  - `components.model`: Status of `best_efficientnetb0.keras` (present, size, loaded).
  - `components.faiss`: Status of FAISS index and metadata file.
  - `components.neo4j`: Active ping to Neo4j instance (returns `"unavailable"` if not configured).
  - `components.groq`: Verifies API key presence (returns `"missing_key"` if unconfigured).
  - `system`: Host platform, Python runtime version, timestamp, memory usage.

### 4.2 Analysis Orchestration Router (`app/routers/analyze.py`)
- **Route:** `POST /analyze`
- **Request Form:** Multipart form data containing:
  - `image`: Image file upload (JPEG, PNG). MIME verified.
  - `patient_id` (`str`): Anonymized clinical patient identifier.
  - `patient_name` (`Optional[str]`): Optional patient name.
  - `patient_age` (`Optional[int]`): Patient age in years.
  - `patient_gender` (`Optional[str]`): Biological gender (`"male"`, `"female"`, `"other"`).
  - `clinical_notes` (`Optional[str]`): Treating clinician observations and staging notes.
- **Response Schema:** `AnalysisResponse` (`app/schemas/analysis.py`)
- **Execution:** Invokes `AnalysisService.run_analysis(...)` asynchronously in a threadpool to prevent blocking the asyncio event loop during TensorFlow operations.

### 4.3 Heatmap Retrieval Router (`app/routers/heatmaps.py`)
- **Route:** `GET /heatmaps/{case_id}/{filename}`
- **Security Validation:** Validates `case_id` against UUID4/alphanumeric regex and restricts `filename` to `(gradcam|gradcam_plus_plus|layercam|hirescam)\.png` to prevent path traversal attacks (`../`).
- **Response:** `FileResponse(media_type="image/png")` streaming raw heatmap bytes.

---

## 5. Domain Service Architectures

### 5.1 Vision Service (`app/services/vision_service.py`)
- **Pattern:** Lazy-loaded singleton. Model is loaded once on first inference or warmup and cached in memory.
- **Inference Method:** `predict(image_bytes: bytes) -> tuple[float, str, float]`
- **Output:** Raw sigmoid probability, predicted class label (`"Oral Squamous Cell Carcinoma (OSCC)"` or `"Normal / Non-Cancerous Tissue"`), and confidence score.

### 5.2 XAI Service (`app/services/xai_service.py`)
- **Model Sharing:** Reuses the loaded TensorFlow model directly from `VisionService` via gradient tape; does not load duplicate model weights.
- **Method Execution:** Computes all four CAM variants in a single pass:
  - `generate_all_heatmaps(image_array, original_image, case_id) -> dict[str, str]`
- **Storage:** Blends heatmaps using `cv2.applyColorMap(..., cv2.COLORMAP_JET)` at 40% opacity with the original histopathology tile and writes PNGs directly to `artifacts/{case_id}/`.

### 5.3 RAG Service (`app/services/rag_service.py`)
- **Model:** `SentenceTransformer("all-MiniLM-L6-v2")` loaded lazily.
- **Search Method:** `retrieve_evidence(query: str, top_k: int = 3) -> list[EvidenceChunk]`
- **Fallback:** If FAISS index is unreadable or missing, returns an empty list gracefully without throwing an uncaught 500 error.

### 5.4 Graph Service (`app/services/graph_service.py`)
- **Driver:** `neo4j.GraphDatabase.driver` using AuraDB bolt connection with SSL encryption.
- **Traversal Method:** `get_disease_context(disease_name: str) -> dict` executes Cypher querying associated risk factors, stages, and pathological criteria.
- **Persistence Method:** `store_case_prediction(case_id, patient_id, prediction, confidence, heatmaps)` records clinical audit trails.
- **Degradation:** Catches `ServiceUnavailable`, `AuthError`, and missing credentials, returning empty context dictionaries and logging warnings.

### 5.5 Report Service (`app/services/report_service.py`)
- **LLM Client:** `groq.Groq` initialized with `settings.GROQ_API_KEY`.
- **Generation Method:** `generate_clinical_report(...) -> ClinicalReport`
- **Medical Prompt Bounding:** System prompt strictly bounds clinical reasoning:
  - Enforces that histopathology classifications are computer-assisted indications requiring pathologist sign-off.
  - Contextualizes XAI feature attribution regions.
  - Cross-references retrieved PubMed literature citations.
- **Fallback:** If API key is missing or call fails, produces a structured template fallback report stating LLM generation was bypassed due to service unavailability.

### 5.6 Analysis Orchestration Service (`app/services/analysis_service.py`)
Coordinates the pipeline in 5 deterministic steps:
1. Generates `case_id` (`CASE-<UUID4>`).
2. Calls `VisionService.predict()` to obtain classification and raw score.
3. Calls `XAIService.generate_all_heatmaps()` to persist and retrieve heatmap URLs.
4. Executes concurrent context retrieval:
   - RAG literature search via `RAGService`.
   - Neo4j graph context retrieval via `GraphService`.
5. Synthesizes medical report via `ReportService` and persists case in Neo4j.
6. Returns comprehensive `AnalysisResponse` object.

---

## 6. Error Handling & Graceful Degradation Strategy

| Failure Scenario | Service Impacted | System Behavior | HTTP Response Code |
| :--- | :--- | :--- | :--- |
| **Invalid Image Upload** | `VisionService` | Rejects non-image bytes or unreadable formats | `HTTP 400 Bad Request` |
| **Missing Model File** | `VisionService` | Logs fatal error on startup; returns clean error on call | `HTTP 500 Internal Error` |
| **FAISS Index Unavailable** | `RAGService` | Logs warning; returns empty literature evidence list | `HTTP 200 OK` (Degraded) |
| **Neo4j Offline / Unset** | `GraphService` | Logs warning; bypasses graph traversal & storage | `HTTP 200 OK` (Degraded) |
| **Groq API Limit / Unset** | `ReportService` | Generates deterministic template clinical report | `HTTP 200 OK` (Degraded) |
| **Path Traversal Attack** | `HeatmapRouter` | Regex rejection of `../` or unknown filenames | `HTTP 404 Not Found` |
