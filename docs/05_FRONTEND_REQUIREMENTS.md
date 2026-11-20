# 05. Frontend Architecture & UI/UX Requirements

**Project:** GAN-based Oral Cancer Detection with GraphRAG and Grad-CAM  
**Target Stack:** React 18+, TypeScript, Vite, Tailwind CSS  
**Audit Date:** November 2026  
**Auditor:** Antigravity AI  

---

## 1. Objective & Vision

The objective is to replace the legacy single-file HTML frontend embedded within the Colab notebook with a **modern, high-performance, clinical-grade Research Console** built using **React, TypeScript, and Vite**.

The reference HTML implementation provided functional baseline features (file upload, prediction gauge, tabbed outputs). The new frontend will elevate this with:
- Strict TypeScript type safety matching backend API schemas.
- High-aesthetic dark medical/scientific theme using Tailwind CSS.
- Interactive multi-method XAI visualization (side-by-side comparison, opacity slider, toggle between raw heatmap and overlay).
- True interactive Knowledge Graph visualization (interactive node-link graph using force simulation or Cytoscape) instead of raw JSON dump.
- Structured Markdown report viewer with clean section navigation and one-click PDF/text export.
- Real-time backend connectivity and health indicator.

---

## 2. Reference UI Deconstruction

Analysis of the legacy template (`reference_ui.html`) identifies the following core UI components that must be modernized:

| Legacy Component | Legacy Behavior | Modernized React + Vite Equivalent |
|---|---|---|
| **Header & Brand** | Static HTML brand logo + CSS pulsating green dot | Responsive navbar with system status indicator polling `GET /health` |
| **Hero Banner** | Static gradient banner with technology tags | Collapsible quick-start guide and architecture overview banner |
| **Dropzone** | HTML5 drag-and-drop with basic `<input type="file">` | Accessible drag-and-drop zone with instant image preview, dimensions audit, file size validator, and clear button |
| **Case Metadata Form** | 6 text fields in a 2-column grid | Polished clinical input form with pre-filled dropdowns (Sex, Tobacco, Alcohol, Common Lesion Sites, Magnification) and free-text research question |
| **Score Indicator** | Conic-gradient CSS ring displaying continuous OSCC score | Animated SVG radial gauge showing continuous score, threshold marker line (`0.850266`), and categorical verdict pill (OSCC vs Normal) |
| **XAI Panel** | 2-column grid of static images with textual stats | Interactive 4-method comparator (Grad-CAM, Grad-CAM++, LayerCAM, HiResCAM) with heatmap/overlay toggle, zoom modal, and pairwise Pearson correlation matrix |
| **Research Report** | Raw `<pre>` text tag | Rich Markdown renderer with typography, collapsible sections, citation pills, and clean copy/export |
| **Literature Evidence** | Basic div cards with external links | Filterable evidence cards sorted by semantic similarity score, featuring PMC citations, paper metadata, and direct source links |
| **Knowledge Graph** | Raw formatted JSON text string (`JSON.stringify`) | **Interactive 2D Canvas Force-Directed Network Graph** rendering Disease, Feature, and Paper nodes with zoom/pan and node inspection tooltips |
| **Disclaimer** | Small footer paragraph | Prominent scientific research disclaimer banner emphasizing investigational use only |

---

## 3. Technology Stack Recommendation

- **Core Framework:** React 18+ (Functional Components & Hooks)
- **Language:** TypeScript 5+ (Strict Mode)
- **Build Tool:** Vite 5+ (Fast HMR, optimized production rollup)
- **Styling:** Tailwind CSS + `clsx` / `tailwind-merge`
- **Iconography:** Lucide React (`lucide-react`)
- **Data Fetching:** Axios or TanStack Query (React Query)
- **Markdown Rendering:** `react-markdown` + `remark-gfm`
- **Graph Visualization:** `react-force-graph-2d` or lightweight SVG Force-Directed Simulation (D3-force)
- **Image Comparison:** Custom interactive overlay slider component

---

## 4. Component Hierarchy

```text
src/
├── assets/                         # Static icons and logos
├── components/
│   ├── layout/
│   │   ├── Navbar.tsx              # Brand logo, title, and backend connection badge
│   │   ├── Footer.tsx              # Academic credits and institutional disclaimers
│   │   └── DisclaimerModal.tsx     # Medical research disclaimer acknowledgment
│   ├── analysis/
│   │   ├── CaseInputForm.tsx       # Image dropzone + patient context inputs
│   │   ├── Dropzone.tsx            # Drag-and-drop file upload with preview
│   │   ├── PatientContextInputs.tsx# Age, sex, risk factors, lesion site, magnification
│   │   └── PredictionGauge.tsx     # Radial score ring, threshold comparison, confidence
│   ├── xai/
│   │   ├── XAIContainer.tsx        # 4-method grid and view switcher
│   │   ├── XAICard.tsx             # Single method card (overlay, heatmap, stats)
│   │   ├── OverlaySlider.tsx       # Interactive before/after opacity comparison
│   │   └── CorrelationMatrix.tsx   # Pairwise Pearson agreement table
│   ├── report/
│   │   ├── ReportViewer.tsx        # Structured Markdown report renderer
│   │   └── ExportReportButton.tsx  # Download formatted TXT / Print to PDF
│   ├── literature/
│   │   ├── LiteratureList.tsx      # Ranked PMC literature evidence cards
│   │   └── EvidenceCard.tsx        # Single chunk card with similarity badge and PMC link
│   └── graph/
│       ├── KnowledgeGraphView.tsx  # Force-directed interactive node-link graph
│       └── GraphNodeDetail.tsx     # Drawer/card showing selected node attributes
├── hooks/
│   ├── useHealthCheck.ts           # Polls GET /health for backend readiness
│   └── useAnalyzeCase.ts           # Handles multipart upload and analysis state
├── services/
│   └── api.ts                      # Axios client configured with base URL and timeout
├── types/
│   └── api.ts                      # Strict TypeScript interfaces for all payloads
├── App.tsx                         # Main single-page application dashboard
└── main.tsx                        # Vite entrypoint
```

---

## 5. Strict TypeScript Contracts (`src/types/api.ts`)

```typescript
export interface HealthResponse {
  status: 'ok' | 'degraded' | 'error';
  cnn: boolean;
  faiss: boolean;
  neo4j: boolean;
  groq: boolean;
  groq_model: string;
  model: string;
  threshold: number;
  xai_methods: string[];
}

export interface PatientContext {
  age: string;
  sex: string;
  tobacco: string;
  alcohol: string;
  lesion_site: string;
  magnification: string;
}

export interface XAIMethodStats {
  min: number;
  max: number;
  mean: number;
  std: number;
  q90: number;
  fraction_at_or_above_0_5: number;
}

export interface XAIMethodResult {
  status: 'ok' | 'failed';
  heatmap_path: string | null;
  heatmap_url: string | null;
  overlay_path: string | null;
  overlay_url: string | null;
  normalization: string;
  statistics?: XAIMethodStats;
  error?: string;
}

export interface PairwiseSimilarity {
  pearson_correlation: number | null;
  cosine_similarity: number | null;
}

export interface XAISummary {
  target: string;
  prediction_equivalence_verified: boolean;
  methods: Record<'Grad-CAM' | 'Grad-CAM++' | 'LayerCAM' | 'HiResCAM', XAIMethodResult>;
  pairwise_similarity: Record<string, PairwiseSimilarity>;
  scope_note: string;
}

export interface GraphNodeContext {
  disease: string;
  relationship: string;
  node_labels: string[];
  node_name: string | null;
  node_title: string | null;
  paper_id: string | null;
  year: number | null;
  query_overlap: number;
}

export interface LiteratureEvidenceChunk {
  chunk_id: string;
  paper_id: string;
  year: number;
  title: string;
  authors: string;
  source_url: string;
  chunk_index: number;
  text: string;
  similarity: number;
  graph_entity_matches?: Array<{
    node_labels: string[];
    node_name: string | null;
    relationship: string;
  }>;
}

export interface GroqReport {
  status: 'ok' | 'error';
  provider: string;
  model: string;
  generated_at: string;
  text?: string;
  error?: {
    code: string;
    message: string;
  };
}

export interface AnalysisResponse {
  case_id: string;
  filename: string;
  patient_context: PatientContext;
  research_question: string;
  prediction: 'OSCC' | 'Normal';
  class_index: 0 | 1;
  oscc_probability: number;
  threshold: number;
  decision_rule: string;
  confidence: number;
  confidence_percent: number;
  xai: XAISummary;
  graph_saved: boolean;
  graph_context: GraphNodeContext[];
  retrieval_query: string;
  literature_evidence: LiteratureEvidenceChunk[];
  errors: Array<{ stage: string; error: string }>;
  scope_note: string;
  report: GroqReport;
}
```

---

## 6. Implementation Steps for Next Phase

Upon user approval of this audit:
1. **Backend Extraction:** Scaffold a standalone `backend/` directory, create `requirements.txt`, configure `.env`, and implement production FastAPI routes.
2. **Frontend Scaffolding:** Initialize `frontend/` using Vite with React + TypeScript template.
3. **Integration Testing:** Connect Vite development server (`http://localhost:5173`) to FastAPI backend (`http://localhost:8000`) with CORS enabled.
4. **Interactive Knowledge Graph:** Implement interactive visual rendering of Neo4j graph nodes.
