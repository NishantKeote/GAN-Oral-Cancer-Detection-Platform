# 02. System Architecture

**Project:** Multimodal Oral Cancer Detection Platform with GraphRAG & Grad-CAM  
**Document:** System & Component Architecture  
**Auditor / Architect:** Antigravity AI  
**Date:** November 2026  

---

## 1. High-Level Architecture

The platform follows a decoupled, service-oriented architecture designed to separate heavy deep learning inference, vector retrieval, and knowledge-graph operations from the user interface.

```mermaid
flowchart TB
    subgraph ClientLayer [Client Presentation Layer]
        SPA[React 18 + TypeScript + Vite SPA]
        LegacyUI[Legacy Embedded Notebook UI - Deprecated]
    end

    subgraph APILayer [Application Gateway & API Layer]
        FastAPI[FastAPI ASGI Application :8000]
        CORS[CORS Middleware - localhost:5173 / 3000]
        Lifespan[Lifespan Context Manager]
        RouterHealth[GET /health]
        RouterAnalyze[POST /analyze]
        RouterHeatmaps[GET /heatmaps/{case_id}/{filename}]
    end

    subgraph ServiceLayer [Core Business & ML Service Layer]
        Orch[AnalysisService]
        Vision[VisionService - EfficientNetB0]
        XAI[XAIService - 4 Attribution Methods]
        RAG[RAGService - FAISS + MiniLM]
        Graph[GraphService - Neo4j Driver]
        Report[ReportService - Groq LLM]
    end

    subgraph StorageLayer [Local Storage & Model Checkpoints]
        ModelFile[models/best_efficientnetb0.keras]
        FAISSIndex[knowledge_base/oscc_literature.faiss]
        MetaJSON[knowledge_base/chunk_metadata.json]
        Artifacts[backend/artifacts/{case_id}/*.png]
    end

    subgraph ExternalCloud [External Managed Services]
        Neo4jDB[(Neo4j AuraDB / Bolt Cloud)]
        GroqAPI[Groq Cloud LLM Inference]
        HuggingFace[HuggingFace Hub - MiniLM Download]
    end

    SPA -->|Multipart Form-Data & REST API| FastAPI
    FastAPI --> CORS
    CORS --> RouterHealth & RouterAnalyze & RouterHeatmaps
    Lifespan -->|Preload On Startup| Vision & RAG & Graph & Report
    
    RouterAnalyze --> Orch
    RouterHeatmaps -->|Stream PNG| Artifacts
    
    Orch --> Vision
    Orch --> XAI
    Orch --> RAG
    Orch --> Graph
    Orch --> Report
    
    Vision -->|Load Weights| ModelFile
    XAI -->|Read Conv Probe| Vision
    XAI -->|Persist PNGs| Artifacts
    RAG -->|Read Index| FAISSIndex
    RAG -->|Read Chunks| MetaJSON
    RAG -.->|Initial Model Pull| HuggingFace
    Graph -.->|Bolt Protocol| Neo4jDB
    Report -.->|REST Completions| GroqAPI
```

---

## 2. Component Architecture

### 2.1. Presentation Layer (Planned)
- **Framework:** React 18+ with TypeScript in strict mode.
- **Build Tool:** Vite with fast Hot Module Replacement (HMR).
- **Communication:** Axios HTTP client dispatching multipart requests to `http://localhost:8000/analyze`.
- **Views:** Upload & Case Configuration, Real-Time Prediction Gauge, 4-Method XAI Multi-View Comparator, Literature Explorer with PMC Links, Interactive Force-Directed Knowledge Graph, and Markdown Research Report Viewer.

### 2.2. API & Routing Layer (`backend/app/routers/`)
- **`app/main.py`:** Configures ASGI application, CORS middleware, global exception handlers, and lifespan lifecycle.
- **`routers/health.py`:** Non-blocking health probe returning active model metadata and boolean readiness flags (`cnn_loaded`, `faiss_loaded`, `neo4j_connected`, `groq_configured`).
- **`routers/analyze.py`:** Multipart file upload endpoint enforcing size caps (20 MB), MIME filtering (`image/*`), patient context normalization, and error translation.
- **`routers/heatmaps.py`:** Static file streamer returning grayscale heatmaps and RGB overlays with regex path traversal protection (`^CASE-[A-F0-9]{10}$`).

### 2.3. Domain Service Layer (`backend/app/services/`)
- **`VisionService`:** Thread-safe singleton model loader. Handles 8-step image preprocessing, intermediate feature probe access, and forward inference.
- **`XAIService`:** Single-pass persistent gradient tape extractor deriving 4 attribution methods (`Grad-CAM`, `Grad-CAM++`, `LayerCAM`, `HiResCAM`), generating normalized overlays and cross-method agreement metrics.
- **`RAGService`:** Manages vector embeddings via `all-MiniLM-L6-v2` (384 dimensions), dynamic case query formulation, and top-5 nearest neighbor search over `oscc_literature.faiss`.
- **`GraphService`:** Neo4j driver connection manager executing parameterized Cypher queries to extract connected medical concepts and persist case records.
- **`ReportService`:** Formats grounded research context, enforces 60,000-character prompt limits, and calls Groq LLM inference under strict disclaimers.
- **`AnalysisService`:** Pipeline coordinator executing all domain services in deterministic dependency order.

---

## 3. End-to-End Multimodal Data Flow

The sequential lifecycle of an analysis request is illustrated below:

```mermaid
sequenceDiagram
    autonumber
    actor User as Researcher / User
    participant Frontend as React SPA (Vite)
    participant Router as POST /analyze
    participant Orch as AnalysisService
    participant Vision as VisionService
    participant XAI as XAIService
    participant RAG as RAGService
    participant Graph as GraphService
    participant Report as ReportService

    User->>Frontend: Selects Histopathology Tile & Enters Context
    Frontend->>Router: Multipart Form Upload
    Router->>Router: Validate size (<=20MB), MIME (image/*), sanitize filename
    Router->>Orch: Dispatch analyze_case(...)

    rect rgb(235, 245, 255)
    Note over Orch,Vision: Stage 1: Computer Vision
    Orch->>Orch: Generate Case UUID ('CASE-XXXXXXXXXX')
    Orch->>Vision: predict(image_bytes)
    Vision->>Vision: Decode -> Resize (224,224) -> Scale float32 -> EfficientNet Preprocess
    Vision->>Vision: Model forward pass -> Sigmoid probability
    Vision->>Vision: Evaluate threshold: OSCC if >= 0.850266 else Normal
    Vision-->>Orch: probability, label, confidence, image_tensor, rgb_image
    end

    rect rgb(255, 240, 240)
    Note over Orch,XAI: Stage 2: Explainable AI Attribution
    Orch->>XAI: generate_attributions(image_tensor, rgb_image, case_id, probability)
    XAI->>XAI: Single-pass GradientTape over 'top_conv'
    XAI->>XAI: Compute Grad-CAM, Grad-CAM++, LayerCAM, HiResCAM
    XAI->>XAI: Min-Max normalize & Blend overlays (58% RGB + 42% Red)
    XAI->>XAI: Save PNGs to backend/artifacts/{case_id}/
    XAI-->>Orch: xai_summary (stats, paths, URLs, similarity matrix)
    end

    rect rgb(240, 255, 240)
    Note over Orch,RAG: Stage 3: Semantic Query Assembly
    Orch->>RAG: build_case_query(label, probability, context, question, xai_summary)
    RAG-->>Orch: Formatted retrieval_query string
    end

    rect rgb(255, 255, 235)
    Note over Orch,Graph: Stage 4: Hybrid Graph-RAG Retrieval
    Orch->>Graph: get_disease_context(retrieval_query)
    alt Neo4j Reachable
        Graph-->>Orch: graph_context (connected nodes & relationships)
    else Neo4j Unreachable / Unconfigured
        Graph-->>Orch: [] (Graceful fallback; append error)
    end

    Orch->>RAG: retrieve_literature(retrieval_query, top_k=5)
    RAG->>RAG: MiniLM 384-dim embedding -> FAISS search -> chunk mapping
    Orch->>RAG: connect_literature_to_graph(literature_chunks, graph_context)
    RAG-->>Orch: literature_evidence with matched graph entities
    end

    rect rgb(250, 235, 255)
    Note over Orch,Report: Stage 5: Persistence & Report Synthesis
    Orch->>Graph: save_case(case_id, filename, context, label, probability, xai, question)
    Graph-->>Orch: graph_saved (True / False fallback)

    Orch->>Report: generate_report(case_id, context, label, probability, xai, question, graph, literature)
    alt Groq Available & Key Configured
        Report-->>Orch: Grounded 7-section Markdown report
    else Groq Unavailable / Quota Error
        Report-->>Orch: Structured error payload (Graceful fallback; append error)
    end
    end

    Orch-->>Router: Assembled AnalysisResponse dictionary
    Router-->>Frontend: 200 OK (Unified JSON response)
    Frontend->>User: Displays Score, 4 Overlays, Literature & Markdown Report
```

---

## 4. External Services & Dependency Analysis

| Service / Dependency | Protocol / Interface | Role in Architecture | Failure Impact | Graceful Degradation Strategy |
|---|---|---|---|---|
| **Local Checkpoint (`models/`)** | Local Filesystem / Keras 3 | EfficientNetB0 classification weights | **Critical:** Cannot classify images | Returns `HTTP 503 Service Unavailable` |
| **Local FAISS Index (`knowledge_base/`)** | Local C++ Index / `faiss-cpu` | 384-dim semantic literature vector store | **Moderate:** Literature retrieval unavailable | Trapped in `try-except`; appends `{'stage': 'literature_retrieval'}` |
| **Hugging Face Hub** | HTTPS | Downloads `all-MiniLM-L6-v2` on initial run | **Low:** Fails if offline on cold boot | Model is cached locally in `%USERPROFILE%\.cache` after first download |
| **Neo4j AuraDB / Instance** | Bolt (`neo4j://`, `neo4j+s://`) | Medical ontology and patient case history | **Low:** Graph traversal and history disabled | Trapped in `try-except`; returns `[]` context and `graph_saved=False` |
| **Groq Cloud API** | HTTPS / REST | LLM research report generation | **Low:** AI narrative synthesis disabled | Trapped in `try-except`; returns structured error payload without failing API |
