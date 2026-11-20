# 05. Frontend Documentation

## 1. Current Status & Implementation State

> [!IMPORTANT]
> ### Implementation Status: PLANNED / NOT IMPLEMENTED
> 
> As established during the Phase 1 repository audit, **no React, TypeScript, or Vite source code currently exists within the workspace**.
> 
> The original research implementation embedded a monolithic, single-page HTML/JavaScript/CSS dashboard directly inside Cell 9 of `notebooks/OSCC_Integrated_GraphRAG_EfficientNet_XAI_FINAL_FIXED.ipynb`.
> 
> This document details both the **deconstructed legacy HTML dashboard** and the **architectural blueprint for the planned React 18+ TypeScript SPA** to be developed in Phase 2.

---

## 2. Deconstruction of Legacy Research Prototype (Notebook Cell 9)

In the original Jupyter Notebook, Cell 9 generated an in-memory HTML page (`index.html`) served by an embedded Uvicorn process.

### 2.1 Legacy Features & Layout
- **Style:** Vanilla CSS with a dark-slate clinical color scheme (`#0f172a`, `#1e293b`).
- **Input:** Basic HTML `<form>` uploading an image with patient metadata.
- **Client Logic:** Standard `fetch('/analyze')` using XMLHttpRequest / Promise chaining.
- **Visual Display:**
  - 4 static image tags displaying heatmaps returned as base64 strings or direct URLs.
  - Plain text block displaying the Groq LLM summary.
  - HTML list showing FAISS literature matches.
  - Textual dump of Neo4j graph relationships.

### 2.2 Technical Limitations of Legacy UI
1. **No State Management:** Refreshing the page wiped all patient history and analysis results.
2. **Synchronous UX Blocking:** The UI froze during the 8–15 second inference and LLM generation window without fine-grained progress feedback.
3. **No Responsive Viewport Controls:** Heatmaps lacked zoom, pan, overlay blending sliders, or side-by-side comparative magnification.
4. **No Formal Type Safety:** Missing TypeScript type definitions resulted in silent rendering failures when API responses were missing optional fields.

---

## 3. Planned Architecture: Modern React 18+ SPA (Phase 2 Blueprint)

The target frontend is structured as a modern Single Page Application (SPA) utilizing React 18, TypeScript, Vite, and Tailwind CSS.

```
frontend/
├── index.html
├── vite.config.ts
├── package.json
├── tsconfig.json
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── assets/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── HealthBadge.tsx
│   │   ├── intake/
│   │   │   ├── PatientForm.tsx
│   │   │   └── ImageDropzone.tsx
│   │   ├── results/
│   │   │   ├── PredictionBanner.tsx
│   │   │   ├── ConfidenceGauge.tsx
│   │   │   ├── XaiComparisonGrid.tsx
│   │   │   ├── HeatmapViewer.tsx
│   │   │   ├── LiteraturePanel.tsx
│   │   │   └── GraphExplorer.tsx
│   │   └── report/
│   │       ├── ClinicalReportView.tsx
│   │       └── ExportPdfButton.tsx
│   ├── hooks/
│   │   ├── useAnalysis.ts
│   │   └── useHealth.ts
│   ├── services/
│   │   └── api.ts
│   └── types/
│       ├── api.ts
│       └── patient.ts
```

---

## 4. Component Hierarchy & User Workflow

```
                        ┌────────────────────────────┐
                        │          App.tsx           │
                        └─────────────┬──────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              ▼                                               ▼
       ┌──────────────┐                              ┌─────────────────┐
       │  Header.tsx  │ (Status, Branding)           │   Sidebar.tsx   │ (Case History)
       └──────────────┘                              └─────────────────┘
              │
              ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │                       Main Dashboard View                        │
   ├─────────────────────────────────┬────────────────────────────────┤
   │        Intake Column            │         Results Column         │
   ├─────────────────────────────────┼────────────────────────────────┤
   │ 1. PatientForm.tsx              │ 1. PredictionBanner.tsx        │
   │    - ID, Age, Gender, Notes     │    - Diagnosis & Risk Meter    │
   │                                 │                                │
   │ 2. ImageDropzone.tsx            │ 2. XaiComparisonGrid.tsx       │
   │    - Drag & drop 224x224 tile   │    - 4 CAM Overlays + Slider   │
   │    - Client-side EXIF strip     │                                │
   │    - Canvas thumbnail preview   │ 3. GraphExplorer.tsx           │
   │                                 │    - Neo4j Knowledge Entities  │
   │ 3. Submit / Cancel Controls     │                                │
   │    - Optimistic progress state  │ 4. LiteraturePanel.tsx         │
   │                                 │    - Top-3 FAISS Evidence      │
   │                                 │                                │
   │                                 │ 5. ClinicalReportView.tsx      │
   │                                 │    - Formatted Medical Report  │
   │                                 │    - PDF / Print Actions       │
   └─────────────────────────────────┴────────────────────────────────┘
```

---

## 5. UI Component Specifications

### 5.1 Patient Intake & Image Dropzone (`ImageDropzone.tsx`)
- **Drag-and-Drop:** Accepts `.jpg`, `.jpeg`, `.png`, and `.tif`.
- **Validation:** 
  - Max file size: 25 MB.
  - Image dimension preview and aspect ratio warning for non-square tiles.
  - Client-side EXIF/TIFF tag stripping for patient privacy.
- **Micro-Interaction:** Immediate responsive thumbnail preview rendered to an HTML5 canvas.

### 5.2 Diagnostic Prediction Banner (`PredictionBanner.tsx`)
- **Class Rendering:**
  - High Malignancy Risk (`p >= 0.850266`): Crimson red badge (`#dc2626`) labeled `"Oral Squamous Cell Carcinoma (OSCC)"`.
  - Non-Cancerous (`p < 0.850266`): Emerald green badge (`#16a34a`) labeled `"Normal / Non-Cancerous Tissue"`.
- **Confidence Gauge (`ConfidenceGauge.tsx`):** Circular SVG or radial gauge visualizing both raw model probability and calibrated decision confidence.

### 5.3 XAI Comparison Grid (`XaiComparisonGrid.tsx`)
- **4-Method View:** Side-by-side or tabbed layout presenting:
  1. Original Tile
  2. Grad-CAM (Broad regional localization)
  3. Grad-CAM++ (Dense multi-region weighting)
  4. LayerCAM (Cellular-level fine spatial details)
  5. HiResCAM (Element-wise unweighted gradient attribution)
- **Interactive Controls:**
  - Synchronized Pan & Zoom: Moving the cursor or zooming one tile magnifies all 4 heatmaps synchronously.
  - Opacity Slider: Continuous blending slider ($0.0 \to 1.0$) between the raw histopathology tile and the heatmap overlay.
  - Method Tooltips: Popover explanations detailing the mathematical formula and clinical interpretation of each attribution method.

### 5.4 GraphRAG Literature & Knowledge Explorer (`LiteraturePanel.tsx`, `GraphExplorer.tsx`)
- **Literature Matches:** Accordion cards displaying paper title, publication year, authors, similarity percentage, matched excerpt, and direct hyperlinked DOI/PubMed URL.
- **Ontology Explorer:** Interactive node graph rendering disease relationships (`Histological Subtype`, `Risk Factors`, `Staging Criteria`) retrieved from Neo4j.

### 5.5 Clinical Report View (`ClinicalReportView.tsx`)
- **Rendering:** Structured clinical summary formatted with Markdown syntax.
- **Export Capabilities:** 
  - Print-ready CSS media query (`@media print`).
  - One-click PDF generation embedding patient metadata, predicted diagnosis, all four XAI heatmaps, and retrieved literature citations.
- **Legal Disclaimer:** Prominent footer indicating computer-assisted diagnostic research software status.

---

## 6. Frontend TypeScript Interfaces & API Contracts

```typescript
export interface AnalysisRequest {
  image: File;
  patientId: string;
  patientName?: string;
  patientAge?: number;
  patientGender?: 'male' | 'female' | 'other';
  clinicalNotes?: string;
}

export interface HeatmapArtifacts {
  gradcam: string;
  gradcam_plus_plus: string;
  layercam: string;
  hirescam: string;
}

export interface LiteratureEvidence {
  chunk_id: string;
  paper_id: string;
  title: string;
  authors: string;
  year: number;
  source_url: string;
  similarity_score: number;
  text: string;
}

export interface AnalysisResponse {
  case_id: string;
  patient_id: string;
  timestamp: string;
  prediction: {
    predicted_class: 'Oral Squamous Cell Carcinoma (OSCC)' | 'Normal / Non-Cancerous Tissue';
    probability: number;
    confidence: number;
    threshold_applied: number;
  };
  heatmaps: HeatmapArtifacts;
  literature_evidence: LiteratureEvidence[];
  graph_context: Record<string, any>;
  clinical_report: {
    summary: string;
    diagnostic_impression: string;
    xai_findings: string;
    literature_correlation: string;
    recommendations: string[];
  };
  status: 'completed' | 'degraded';
}
```

---

## 7. UI State Management & Error Handling

1. **State Engine:** TanStack React Query v5 for API caching, mutation states, and asynchronous retry logic.
2. **Optimistic Loading:** Displays a staged progress indicator during analysis:
   - Step 1: Preprocessing & EfficientNetB0 Inference (15%)
   - Step 2: Multi-Method XAI Computation (40%)
   - Step 3: FAISS Semantic Literature Retrieval (60%)
   - Step 4: Neo4j Knowledge Graph Traversal (80%)
   - Step 5: Groq LLM Medical Synthesis (100%)
3. **Graceful Degraded State:** If Neo4j or Groq fails, the UI displays warning badges on the affected cards while still rendering the primary diagnosis and XAI heatmaps without interruption.
