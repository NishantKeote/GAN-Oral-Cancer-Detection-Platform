# 04. Backend API Audit & Refactoring Blueprint

**Project:** GAN-based Oral Cancer Detection with GraphRAG and Grad-CAM  
**Audit Date:** November 2026  
**Auditor:** Antigravity AI  

---

## 1. Existing Backend Implementation Audit

The existing backend is implemented in **Cell 9 of `notebooks/OSCC_Integrated_GraphRAG_EfficientNet_XAI_FINAL_FIXED.ipynb`**. It uses **FastAPI 2.0** with **Uvicorn** and **Pyngrok** to expose endpoints from a Google Colab session.

### 1.1. Current Architectural Deficiencies
1. **Trapped in Jupyter Notebook:** The backend cannot be run outside of Google Colab in its current state.
2. **Colab-Specific Secret Management:** Uses `google.colab.userdata.get(...)` instead of standard environment variables or `.env` files.
3. **Hardcoded Google Drive Paths:** Paths such as `/content/drive/MyDrive/OSCC V2/best_efficientnetb0.keras` and `/content/oscc_graphrag_artifacts` are hardcoded.
4. **Monolithic Global State:** Model, FAISS index, SentenceTransformer embedder, Neo4j driver, and Groq client are initialized directly in the global notebook namespace without lifespan lifecycle management or dependency injection.
5. **No Static Typing / Pydantic Schemas:** Form inputs are accepted as raw `str` arguments without strict Pydantic model schemas for validation.
6. **No Packaging:** Lacks a standalone entrypoint (`python -m uvicorn app.main:app`), `requirements.txt`, or containerization.

---

## 2. API Endpoint Specifications

### 2.1. `GET /health`
- **Purpose:** Health check and readiness probe.
- **Request:** None.
- **Response Format:** `application/json`
- **Response Schema:**
  ```json
  {
    "status": "ok",
    "cnn": true,
    "faiss": true,
    "neo4j": true,
    "groq": true,
    "groq_model": "openai/gpt-oss-20b",
    "model": "EfficientNetB0",
    "threshold": 0.850266,
    "xai_methods": ["Grad-CAM", "Grad-CAM++", "LayerCAM", "HiResCAM"]
  }
  ```

---

### 2.2. `POST /analyze`
- **Purpose:** Primary multimodal inference endpoint. Decodes uploaded histopathology tile, computes continuous OSCC sigmoid score, generates 4 XAI heatmaps, retrieves FAISS literature chunks, queries Neo4j graph context, persists case records, and synthesizes a Groq research report.
- **Content-Type:** `multipart/form-data`
- **Request Parameters:**
  | Field Name | Type | Required? | Constraints / Example |
  |---|---|---|---|
  | `image` | `UploadFile` (Binary) | **Required** | Max 20 MB; MIME type must begin with `image/` |
  | `age` | `string` | Optional | e.g., `"58"` |
  | `sex` | `string` | Optional | `"Male"` / `"Female"` / `"Other"` |
  | `tobacco` | `string` | Optional | `"Yes, 20 pack-years"` / `"No"` |
  | `alcohol` | `string` | Optional | `"Moderate"` / `"None"` |
  | `lesion_site` | `string` | Optional | `"Lateral border of tongue"`, `"Buccal mucosa"` |
  | `magnification`| `string` | Optional | `"400x"`, `"100x"`, `"40x"` |
  | `research_question` | `string` | Optional | Custom query guiding RAG and report synthesis |

- **Response Format:** `application/json` (Status `200 OK`)
- **Response Payload Structure:**
  ```json
  {
    "case_id": "CASE-4F8A9C12DE",
    "filename": "OSCC_400x_tile.png",
    "patient_context": {
      "age": "58",
      "sex": "Male",
      "tobacco": "Yes",
      "alcohol": "No",
      "lesion_site": "Tongue",
      "magnification": "400x"
    },
    "research_question": "Evaluate keratin pearl formation and invasive front",
    "prediction": "OSCC",
    "class_index": 1,
    "oscc_probability": 0.984215,
    "threshold": 0.850266,
    "decision_rule": "OSCC when OSCC sigmoid score >= 0.850266; otherwise Normal",
    "confidence": 0.984215,
    "confidence_percent": 98.42,
    "xai": {
      "target": "continuous OSCC sigmoid score",
      "prediction_equivalence_verified": true,
      "methods": {
        "Grad-CAM": {
          "status": "ok",
          "heatmap_path": "artifacts/CASE-4F8A9C12DE/grad_cam.png",
          "heatmap_url": "/heatmaps/CASE-4F8A9C12DE/grad_cam.png",
          "overlay_path": "artifacts/CASE-4F8A9C12DE/grad_cam_overlay.png",
          "overlay_url": "/heatmaps/CASE-4F8A9C12DE/grad_cam_overlay.png",
          "normalization": "Per-image min-max to [0,1] after method ReLU; constant maps are zero.",
          "statistics": {
            "min": 0.0,
            "max": 1.0,
            "mean": 0.324,
            "std": 0.281,
            "q90": 0.785,
            "fraction_at_or_above_0_5": 0.284
          }
        },
        "Grad-CAM++": { "...": "..." },
        "LayerCAM": { "...": "..." },
        "HiResCAM": { "...": "..." }
      },
      "pairwise_similarity": {
        "Grad-CAM vs Grad-CAM++": { "pearson_correlation": 0.912, "cosine_similarity": 0.934 },
        "Grad-CAM vs LayerCAM": { "pearson_correlation": 0.887, "cosine_similarity": 0.905 },
        "Grad-CAM vs HiResCAM": { "pearson_correlation": 0.862, "cosine_similarity": 0.881 },
        "Grad-CAM++ vs LayerCAM": { "pearson_correlation": 0.923, "cosine_similarity": 0.941 },
        "Grad-CAM++ vs HiResCAM": { "pearson_correlation": 0.899, "cosine_similarity": 0.918 },
        "LayerCAM vs HiResCAM": { "pearson_correlation": 0.954, "cosine_similarity": 0.967 }
      },
      "scope_note": "Attribution only; not lesion detection, pathology confirmation, or evidence of cancer."
    },
    "graph_saved": true,
    "graph_context": [
      {
        "disease": "Oral Squamous Cell Carcinoma",
        "relationship": "ASSOCIATED_WITH",
        "node_labels": ["HistologicalFeature"],
        "node_name": "Keratin Pearls",
        "node_title": null,
        "paper_id": "PMC8631280",
        "year": 2021,
        "query_overlap": 3
      }
    ],
    "retrieval_query": "oral squamous cell carcinoma histopathology research evidence...",
    "literature_evidence": [
      {
        "chunk_id": "PMC8631280_chunk_0000",
        "paper_id": "PMC8631280",
        "year": 2021,
        "title": "The Impact of Histopathological Features on the Prognosis of Oral Squamous Cell Carcinoma: A Comprehensive Review and Meta-Analysis",
        "authors": "Dolens et al.",
        "source_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8631280/",
        "chunk_index": 0,
        "text": "Extracted text content from PubMed Central...",
        "similarity": 0.7842,
        "graph_entity_matches": [
          {
            "node_labels": ["HistologicalFeature"],
            "node_name": "Keratin Pearls",
            "relationship": "ASSOCIATED_WITH"
          }
        ]
      }
    ],
    "errors": [],
    "scope_note": "The model score is not clinical probability. Heatmaps indicate model attribution only and do not prove pathology. Graph and literature provide research context, not specimen-specific confirmation.",
    "report": {
      "status": "ok",
      "provider": "Groq",
      "model": "openai/gpt-oss-20b",
      "generated_at": "2026-11-20T05:02:18.123456+00:00",
      "text": "### Case Summary\n...\n### Model Prediction\n...\n### XAI Attribution\n...\n### Limitations\n..."
    }
  }
  ```

---

### 2.3. `GET /heatmaps/{case_id}/{filename}`
- **Purpose:** Serves generated PNG heatmaps and overlays.
- **Path Parameters:**
  - `case_id`: String matching regex `^CASE-[A-F0-9]{10}$`
  - `filename`: Must be in `{grad_cam, grad_cam_plus_plus, layer_cam, hires_cam}{.png, _overlay.png}`
- **Security Check:** Strictly prevents path traversal attacks (`../`).
- **Response:** `FileResponse(media_type="image/png")`

---

## 3. Recommended Production Backend Architecture

To support the new React + Vite frontend, the backend code should be extracted from the notebook into a production-grade FastAPI service structured as follows:

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app factory, CORS, exception handlers
│   ├── config.py                   # Pydantic BaseSettings (.env loading, thresholds, model paths)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py               # Aggregated API router
│   │   └── v1/
│   │       ├── health.py           # Health and readiness endpoints
│   │       ├── analyze.py          # /analyze endpoint
│   │       └── heatmaps.py         # Static heatmap file streaming
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── health.py               # Health check response schemas
│   │   ├── analyze.py              # Case input schemas and complete analysis response schemas
│   │   └── xai.py                  # XAI method stats and similarity schemas
│   └── services/
│       ├── __init__.py
│       ├── model_service.py        # EfficientNetB0 loader and inference probe
│       ├── xai_service.py          # 4-method gradient attribution math and image generation
│       ├── faiss_service.py        # SentenceTransformer embedder and FAISS index manager
│       ├── neo4j_service.py        # Neo4j driver, Cypher execution, and graceful offline fallback
│       └── groq_service.py         # Grounded prompt builder and Groq LLM client
├── artifacts/                      # Working directory for case heatmaps and overlays
├── requirements.txt                # Pinned production Python dependencies
└── .env.example                    # Template for GROQ_API_KEY, NEO4J_*, etc.
```

### Key Refactoring Improvements:
1. **Configurable CORS:** Add explicit support for `http://localhost:5173` (Vite dev server) and `http://127.0.0.1:5173`.
2. **Graceful Degradation:** If Neo4j or Groq is unreachable or credentials are not configured, the backend will still execute inference and XAI generation, returning structured degradation notices instead of crashing.
3. **Local Artifact Management:** Replaces `/content/oscc_graphrag_artifacts` with a configurable local `./artifacts` directory.
