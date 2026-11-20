# 11. Development History & Strategic Roadmap

## 1. Chronological Development History

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               Chronological Timeline                                   │
├────────────────────┬───────────────────────────────────────────────────────────────────┤
│ Research Phase     │ Monolithic Jupyter Notebook prototyping (Cell 1 through Cell 9)   │
│ Phase 1 Audit      │ Systematic inspection of models, FAISS index, and dependencies    │
│ Phase 1A           │ Backend scaffolding, config, logging, and core directory structure │
│ Phase 1B & 1B.1    │ Foundation code review, path resolution fix & response models     │
│ Phase 1C           │ Extraction of VisionService (EfficientNetB0 lazy-loading)         │
│ Phase 1D           │ Extraction of XAIService (Grad-CAM, ++, LayerCAM, HiResCAM)      │
│ Phase 1E           │ Extraction of RAGService (MiniLM bi-encoder + FAISS IndexFlatIP)  │
│ Phase 1F           │ Extraction of GraphService (Neo4j) & ReportService (Groq LLM)     │
│ Phase 1G           │ Orchestration assembly in AnalysisService & endpoint wiring       │
│ Documentation      │ Comprehensive source-code grounded technical documentation suite  │
└────────────────────┴───────────────────────────────────────────────────────────────────┘
```

---

## 2. Key Technical Decisions & Architectural Trade-Offs

### 2.1 Decoupling the Research Monolith into Modular Services
- **Context:** The original research resided entirely within `notebooks/OSCC_Integrated_GraphRAG_EfficientNet_XAI_FINAL_FIXED.ipynb`, executing a local Uvicorn instance directly within notebook cells.
- **Decision:** Extracted business logic into six dedicated services (`vision_service.py`, `xai_service.py`, `rag_service.py`, `graph_service.py`, `report_service.py`, `analysis_service.py`).
- **Rationale:** Monolithic notebooks cannot be version-controlled cleanly, cannot be containerized for horizontal scaling, and lack automated testability.

### 2.2 Shared Model Instance between Vision and XAI Services
- **Context:** `XAIService` requires access to convolutional feature activations and gradients from `EfficientNetB0`.
- **Decision:** `XAIService` accepts the loaded model instance directly from `VisionService` rather than loading a second copy into GPU/CPU memory.
- **Rationale:** Cuts memory consumption by 50% (~35 MB model footprint preserved) and eliminates redundant graph construction.

### 2.3 Dynamic Path Anchoring for Dual-Directory Execution
- **Context:** Developers and deployment scripts frequently execute `uvicorn` from either the repository root or within the `backend/` directory, causing relative path resolution failures for `models/` and `knowledge_base/`.
- **Decision:** Implemented dynamic path anchoring in `backend/app/config.py` using parent directory resolution.
- **Rationale:** Guarantees deterministic asset loading regardless of working directory.

### 2.4 Graceful Degradation Architecture
- **Context:** Neo4j AuraDB and Groq Cloud LLM depend on external network connectivity, third-party cloud uptime, and API keys.
- **Decision:** Wrapped all external database and API calls in try-catch handlers that fall back to deterministic responses (`status="degraded"`).
- **Rationale:** A clinical diagnostic tool must never crash during critical histopathology inference because an auxiliary literature search or LLM summary is temporarily unavailable.

---

## 3. Audit Findings & Resolution Log

| Finding / Discrepancy | Original State | Resolution / Clarification |
| :--- | :--- | :--- |
| **CycleGAN Inconsistency** | Readme files claimed CycleGAN generation (100 epochs, MAE 0.0918) | Verified absent. Documented as theoretical/uncommitted research artifact. Classification operates independently. |
| **Path Resolution Fragility** | Static relative paths broke when running from `backend/` | Fixed in Phase 1B.1 via `_resolve_repo_path()` in `config.py`. |
| **Missing Response Contracts** | Endpoints returned untyped dictionaries | Added explicit Pydantic `HealthResponse` and `AnalysisResponse` models. |
| **Python Version Drift** | Host system running Python 3.14 without TensorFlow | Established strict Python 3.11 requirement due to upstream TensorFlow wheel availability. |

---

## 4. Strategic Engineering Roadmap

```
Phase 1: Backend Extraction (Complete)
   │
   ▼
Phase 2: Modern Frontend Implementation (Q1 2027)
   │ • Build React 18 + TypeScript + Vite SPA
   │ • Implement synchronized 4-method heatmap viewer with pan/zoom
   │ • Build interactive GraphRAG literature drawer
   │ • Client-side DICOM/TIFF pre-processing
   │
   ▼
Phase 3: Whole-Slide Image (WSI) Inference Pipeline (Q2 2027)
   │ • Support multi-gigabyte SVS/NDPI digital pathology slides
   │ • Implement automated tissue segmentation and tile extraction
   │ • Heatmap aggregation and tile-level attention pooling
   │
   ▼
Phase 4: Generative Augmentation / Normalization (Q3 2027)
   │ • Decide whether to formally implement CycleGAN for H&E stain normalization
   │ • Train and serialize generator weights ($G_{A \to B}$)
   │ • Integrate stain normalization as an optional pre-inference step
   │
   ▼
Phase 5: Enterprise Deployment & Clinical Validation (Q4 2027)
   │ • Docker multi-stage containerization & Kubernetes Helm charts
   │ • HIPAA/GDPR compliance audit & TLS 1.3 reverse proxy
   │ • Multi-center prospective clinical trial validation
```
