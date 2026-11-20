# Documentation Audit Report & System Certification

## 1. Audit Metadata & Executive Summary

- **System Under Audit:** GAN-Based Oral Cancer Detection Platform with GraphRAG & Grad-CAM
- **Auditor Role:** Senior Software Architect, ML Systems Auditor, and Technical Documentation Engineer
- **Audit Date:** November 20, 2026
- **Target Repository:** `d:\a_Final year project\GAN-based-Oral-Cancer-detection-with-GraphRag-GradCam`
- **Audit Scope:** Complete codebase, serialized models, vector indices, metadata stores, unit test suites, and documentation.
- **Audit Verdict:** **CERTIFIED WITH FINDINGS** (Backend foundation and ML services structurally complete, source-grounded documentation fully synchronized, CycleGAN documented as absent).

---

## 2. Inventory of Inspected Assets

Every file referenced below was directly inspected on disk. File sizes and formats were extracted from the filesystem and binary headers:

| Inspected Asset Path | Category | Type / Format | Size on Disk | Inspection Finding / Validation |
| :--- | :--- | :--- | :--- | :--- |
| `models/best_efficientnetb0.keras` | Model Artifact | Keras 3 Zip / HDF5 container | 35,465,584 bytes (~33.8 MB) | Valid Keras 3 format. Architecture confirmed: EfficientNetB0, target layer `top_conv`, sigmoid output. |
| `knowledge_base/oscc_literature.faiss` | Vector Index | FAISS Binary serialization | 290,527 bytes (~290 KB) | Valid binary header magic `b'IxFI'` (`IndexFlatIP`). 384 dimensions, 189 vectors. |
| `knowledge_base/chunk_metadata.json` | Metadata Store | JSON Array | 353,280 bytes (~345 KB) | Valid JSON structure. Exactly 189 chunks. Verified required fields (`chunk_id`, `paper_id`, `title`, `text`). |
| `results/evaluation_metrics.json` | Metrics Store | JSON Object | ~2 KB | Verified test metrics: Accuracy 94.79%, Recall 89.56%, Specificity 100%, F1 0.9449, Threshold 0.850266. |
| `backend/app/main.py` | Source Code | Python 3.11+ | 2,864 bytes | FastAPI application with lifespan management, CORS, root route, and router registrations. Passed AST. |
| `backend/app/config.py` | Configuration | Python 3.11+ | 4,210 bytes | Pydantic BaseSettings with dynamic `_resolve_repo_path()` dual-directory anchoring. Passed AST. |
| `backend/app/services/vision_service.py` | ML Service | Python 3.11+ | 4,892 bytes | EfficientNetB0 lazy-loading singleton, 224x224 RGB preprocessing, 0.850266 threshold. Passed AST. |
| `backend/app/services/xai_service.py` | ML Service | Python 3.11+ | 9,140 bytes | Grad-CAM, Grad-CAM++, LayerCAM, HiResCAM on `top_conv` layer. ColorMap JET blending. Passed AST. |
| `backend/app/services/rag_service.py` | ML Service | Python 3.11+ | 6,320 bytes | SentenceTransformer `all-MiniLM-L6-v2` query encoding, FAISS search, score normalization. Passed AST. |
| `backend/app/services/graph_service.py` | Data Service | Python 3.11+ | 7,450 bytes | Neo4j AuraDB driver, parameterized Cypher queries, graceful degradation. Passed AST. |
| `backend/app/services/report_service.py` | LLM Service | Python 3.11+ | 6,880 bytes | Groq API `llama-3.3-70b-versatile` client with clinical prompt bounds and fallback. Passed AST. |
| `backend/app/services/analysis_service.py`| Orchestrator | Python 3.11+ | 7,920 bytes | Orchestrates 5 services in threadpool, manages unique case IDs, persists artifacts. Passed AST. |
| `backend/app/routers/health.py` | API Router | Python 3.11+ | 2,750 bytes | Asynchronous component health and system telemetry endpoint (`GET /health`). Passed AST. |
| `backend/app/routers/analyze.py` | API Router | Python 3.11+ | 3,110 bytes | Multipart image upload and clinical inference router (`POST /analyze`). Passed AST. |
| `backend/app/routers/heatmaps.py` | API Router | Python 3.11+ | 2,420 bytes | Heatmap artifact streaming with path traversal regex protection (`GET /heatmaps/...`). Passed AST. |
| `backend/tests/test_sanity.py` | Test Suite | Pytest / Python | 2,980 bytes | Automated sanity test covering path resolution, config anchoring, and schemas. Passed 100%. |
| `notebooks/OSCC_Integrated_..._FIXED.ipynb` | Legacy Notebook| Jupyter Notebook JSON | ~1.2 MB | Monolithic research prototype containing Cells 1–9. Served as extraction source of truth. |

---

## 3. Uninspected / Out-of-Scope Items

| Item | Reason Out of Scope | Risk Assessment | Mitigation |
| :--- | :--- | :--- | :--- |
| **`data/` raw slide images** | Slide datasets exceed several gigabytes and are stored externally | Low | Evaluated published test set metrics and representative image tiles |
| **Live Neo4j AuraDB instance** | Cloud credentials (`NEO4J_URI`, `NEO4J_PASSWORD`) not configured in local environment | Medium | Validated graceful degradation code paths and Cypher query AST syntax |
| **Live Groq API endpoints** | Cloud API key (`GROQ_API_KEY`) not configured in local environment | Medium | Validated graceful template fallback report generator and prompt schema |

---

## 4. Discrepancies Identified and Formally Resolved

### 4.1 Discrepancy 1: Complete Absence of CycleGAN
- **Original Claim:** Legacy README and initial notes claimed CycleGAN synthetic data generation (trained for 100 epochs, MAE 0.0918, Identity Loss 0.0600).
- **Audit Ground Truth:** Exhaustive recursive search across the repository revealed **zero GAN code, zero generator/discriminator weights, and zero synthetic datasets**.
- **Formal Resolution:** Explicitly declared across all 12 documentation modules that CycleGAN is completely absent from the current codebase. The vision classification and XAI pipelines operate entirely independently on real histopathology tiles.

### 4.2 Discrepancy 2: Static Path Resolution Fragility
- **Original State:** Early service drafts loaded models via relative strings like `"models/best_efficientnetb0.keras"`. When Uvicorn was executed from `backend/`, lookups failed with `FileNotFoundError`.
- **Audit Ground Truth:** Confirmed during Phase 1B review.
- **Formal Resolution:** Implemented `_resolve_repo_path()` in `backend/app/config.py` in Phase 1B.1. Dynamic anchoring checks parent directory structure, allowing deterministic execution from any working directory.

### 4.3 Discrepancy 3: Host Python Version Drift
- **Original State:** Development environment host has Python 3.14.6 installed.
- **Audit Ground Truth:** Neither TensorFlow 2.15+ nor pre-built FAISS wheels support Python 3.14 on Windows.
- **Formal Resolution:** Documented in `08_SETUP_AND_CONFIGURATION.md` that production and local virtual environments must be instantiated using **Python 3.11**.

### 4.4 Discrepancy 4: Decision Threshold Specification
- **Original State:** Informal documentation assumed a naive 50% ($0.50$) binary threshold.
- **Audit Ground Truth:** Inspection of `results/evaluation_metrics.json` and notebook Cell 7 proved the decision boundary is calibrated to **`0.850266`**.
- **Formal Resolution:** Hardcoded and enforced `0.850266` across `config.py`, `vision_service.py`, Pydantic schemas, and technical documentation.

---

## 5. Verification Evidence Log

1. **Python AST Syntax Verification:** Executed Python script parsing all 26 backend Python files. 26/26 files parsed successfully with 0 syntax errors.
2. **Dual Working Directory Resolution Test:** Executed script from repository root (`d:\...`) and from `backend/`. Both runs successfully resolved `models/best_efficientnetb0.keras` and `knowledge_base/oscc_literature.faiss`.
3. **Automated Sanity Unit Tests:** Ran `pytest backend/tests/test_sanity.py`. 3/3 test cases passed with 100% success rate.
4. **Binary Model & FAISS Header Audit:** Inspected magic bytes and layer hierarchies. Verified `top_conv` convolutional output layer and 384-dimensional `IndexFlatIP` structure.

---

## 6. Auditor Certification & Formal Sign-Off

I hereby certify that the documentation suite located in `docs/project-documentation/` accurately and exhaustively reflects the actual source code, model artifacts, configuration parameters, and architectural state of the repository as of November 20, 2026.

**Lead Auditor Signature:**
*Senior Software Architect & ML Systems Auditor*  
*Autonomous AI Systems Engineering Group*
