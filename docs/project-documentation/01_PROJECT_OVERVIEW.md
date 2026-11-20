# 01. Project Overview

**Project Name:** Multimodal Deep Learning Decision-Support Platform for Oral Cancer Detection with GraphRAG and Explainable AI  
**Repository Name:** `GAN-based-Oral-Cancer-detection-with-GraphRag-GradCam`  
**Author / Academic Lead:** Rizwan Ahemad Sayyad  
**Auditor / Architect:** Antigravity AI  
**Documentation Date:** November 2026  
**Status:** In Active Development (Phase 1 Backend Assembled; Frontend Pending)

---

## 1. Project Background & Problem Statement

Oral Squamous Cell Carcinoma (OSCC) represents more than 90% of all oral malignancies worldwide. Early identification and accurate interpretation of histopathological tissue specimens are pivotal for patient prognosis, 5-year survival rates, and surgical planning. However, conventional histopathological evaluation relies on manual microscopic inspection of biopsy sections stained with hematoxylin and eosin (H&E), a process that is time-intensive, subject to inter-observer variability, and often disconnected from contextual biomedical literature.

Recent advancements in computer vision and artificial intelligence have demonstrated significant promise in automated image classification. Nonetheless, deep convolutional neural networks (CNNs) operate primarily as "black boxes," providing diagnostic probabilities without visual attribution or contextual clinical evidence. Furthermore, medical practitioners require explainable justifications and grounded references to peer-reviewed oncological literature when reviewing suspicious specimens.

This project addresses these challenges by developing a unified, multimodal decision-support framework that integrates:
1. **Automated Histopathological Image Classification:** EfficientNetB0 fine-tuned on biopsy image patches.
2. **Explainable AI (XAI) Attribution:** Multi-algorithm gradient-weighted feature localization (`Grad-CAM`, `Grad-CAM++`, `LayerCAM`, `HiResCAM`).
3. **Graph Retrieval-Augmented Generation (GraphRAG):** Hybrid retrieval linking vector search (`FAISS` over PubMed Central literature) with structured medical knowledge graph entities (`Neo4j`).
4. **Grounded Synthesis:** Large Language Model (`Groq`) report generation enforcing clinical guardrails and explicit disclaimers.

---

## 2. Objectives and Scope

### Primary Objectives
- **Automated Screening Support:** Differentiate between normal oral epithelium and OSCC histopathological tissue tiles using transfer learning.
- **Visual Interpretability:** Generate calibrated visual heatmaps and RGB tissue overlays highlighting microscopic morphological regions influencing model predictions.
- **Biomedical Evidence Retrieval:** Semantically retrieve relevant peer-reviewed studies discussing specific histological features (e.g., keratin pearl formation, nuclear pleomorphism, invasive front).
- **Knowledge Graph Entity Linking:** Traverse and store disease-feature relationships in a Neo4j graph database to track patient case history and correlated biomarkers.
- **Production-Grade Architecture:** Transition experimental notebook prototypes into a clean, modular FastAPI service ready for consumption by a modern React + TypeScript web application.

### Scope Boundaries & Academic Disclaimers
> [!IMPORTANT]
> **Investigational Research Tool Only:** This software is developed strictly for academic research and educational evaluation. It is **not a clinically validated diagnostic system** and must never replace licensed pathologists, clinical biopsy examination, or professional oncological staging.

- **Non-Clinical Confidence:** Model scores represent continuous sigmoid outputs on fixed 224×224 image patches, not calibrated probabilities that a patient has cancer.
- **Attribution vs. Segmentation:** XAI heatmaps highlight convolutional feature attribution; they do not delineate clinical lesion boundaries or segment cancerous nuclei.

---

## 3. System Capabilities Matrix

The platform provides seven core capabilities across its pipeline:

| Capability | Module / Component | Technical Implementation | Operational Status |
|---|---|---|---|
| **Image Preprocessing** | `VisionService` | 224×224 bilinear resize, float32 clipping, EfficientNet scaling | **Implemented & Verified** |
| **Tissue Classification** | `VisionService` | Fine-tuned EfficientNetB0 (`models/best_efficientnetb0.keras`) | **Implemented & Verified** |
| **XAI Localization** | `XAIService` | Grad-CAM, Grad-CAM++, LayerCAM, HiResCAM | **Implemented & Verified** |
| **Overlay Rendering** | `XAIService` | 58% RGB tissue + 42% Red Heatmap alpha blend | **Implemented & Verified** |
| **Literature Retrieval** | `RAGService` | FAISS vector search (384-dim, `all-MiniLM-L6-v2`) | **Implemented & Verified** |
| **Knowledge Graph** | `GraphService` | Parameterized Neo4j Cypher traversal & case write | **Implemented (Offline Fallback Verified)** |
| **LLM Synthesis** | `ReportService` | Groq chat completions (`llama-3.3-70b-versatile`) | **Implemented (Offline Fallback Verified)** |
| **REST API Server** | FastAPI Backend | Modular ASGI app with CORS, health, and analyze routes | **Implemented & Verified** |
| **Single-Page UI** | Frontend | Planned React 18 + TypeScript + Vite console | **Planned / Not Yet Implemented** |
| **Synthetic GAN Image Generation** | Generative Module | CycleGAN / WGAN / HistoGAN | **Not Implemented (Artifacts Missing)** |

---

## 4. Research vs. Application Functionality

To ensure transparency across academic evaluation and software engineering:

### A. Original Research Exploration (Notebooks & Results)
- Initial experimentation was conducted in Google Colab across three standalone notebooks (`oral_cancer_detection_EfficientNet_V2.ipynb`, `oscc_efficientnetb0_xai_four_methods.ipynb`, and `OSCC_Integrated_GraphRAG_EfficientNet_XAI_FINAL_FIXED.ipynb`).
- Evaluated on 768 test images from the Kaggle OSCC dataset:
  - **Accuracy:** `94.79%`
  - **Precision:** `100.0%`
  - **Sensitivity (Recall):** `89.56%`
  - **Specificity:** `100.0%`
  - **F1-Score:** `0.9449`
  - **ROC-AUC:** `0.9933`
  - **Optimal Decision Threshold:** `0.850266`

### B. Production Application Layer (`backend/`)
- Extracted monolithic notebook code into an asynchronous, modular architecture separating configuration, domain services, Pydantic schemas, and routers.
- Built-in graceful degradation: if external cloud services (Neo4j Aura or Groq) are offline or unconfigured, the system returns complete classification scores and visual heatmaps without crashing.

---

## 5. Current Implementation Status Summary

```text
[========================================] 100% Phase 1A: Backend Scaffolding & Schemas
[========================================] 100% Phase 1B.1: Path Anchoring & Response Models
[========================================] 100% Phase 1C: EfficientNetB0 Service Extraction
[========================================] 100% Phase 1D: 4-Method XAI Service Extraction
[========================================] 100% Phase 1E: RAG & FAISS Service Extraction
[========================================] 100% Phase 1F: Neo4j & Groq Service Extraction
[========================================] 100% Phase 1G: End-to-End Orchestration & Routers
[----------------------------------------]   0% Phase 2: React + TypeScript + Vite Frontend
```

- **Backend:** Fully scaffolded, modularized, and statically verified with 26 Python files and zero syntax errors.
- **Frontend:** Currently non-existent in the workspace; only legacy HTML template from the notebook exists as a visual reference.
- **GAN / CycleGAN:** Absent from repository code and weights (documented discrepancy).
