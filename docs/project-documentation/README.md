# GAN-Based Oral Cancer Detection Platform — Technical Documentation Suite

Welcome to the comprehensive, source-code-grounded technical documentation repository for the **GAN-Based Oral Cancer Detection Platform with GraphRAG & Explainable AI (XAI)**.

This documentation suite provides a complete, authoritative reference for software engineers, machine learning researchers, clinical evaluators, and system auditors. Every architectural assertion, parameter, and metric documented herein is verified directly against repository source files and research artifacts.

---

## 📚 Master Documentation Index

| # | Document | File Path | Focus Area / Description |
| :-: | :--- | :--- | :--- |
| **01** | **Project Overview** | [01_PROJECT_OVERVIEW.md](01_PROJECT_OVERVIEW.md) | Clinical motivation, problem statement, key components, verified metrics, CycleGAN audit |
| **02** | **System Architecture** | [02_SYSTEM_ARCHITECTURE.md](02_SYSTEM_ARCHITECTURE.md) | High-level topology, end-to-end dataflow, component boundaries, latency budgets |
| **03** | **AI / ML Technical Doc** | [03_AI_ML_TECHNICAL_DOCUMENTATION.md](03_AI_ML_TECHNICAL_DOCUMENTATION.md) | EfficientNetB0, threshold 0.850266, 4 XAI methods, FAISS vector search, CycleGAN audit |
| **04** | **Backend Documentation** | [04_BACKEND_DOCUMENTATION.md](04_BACKEND_DOCUMENTATION.md) | FastAPI framework, config path anchoring, routers, 6 domain services, degradation |
| **05** | **Frontend Documentation** | [05_FRONTEND_DOCUMENTATION.md](05_FRONTEND_DOCUMENTATION.md) | Planned React 18 / TS / Vite SPA blueprint, legacy HTML dashboard deconstruction |
| **06** | **Database & Knowledge Base** | [06_DATABASE_AND_KNOWLEDGE_BASE.md](06_DATABASE_AND_KNOWLEDGE_BASE.md) | FAISS IndexFlatIP (384-dim), Neo4j AuraDB graph ontology, Cypher queries, persistence |
| **07** | **API Reference** | [07_API_REFERENCE.md](07_API_REFERENCE.md) | OpenAPI specifications for `/`, `/health`, `/analyze`, `/heatmaps/...` with cURL examples |
| **08** | **Setup & Configuration** | [08_SETUP_AND_CONFIGURATION.md](08_SETUP_AND_CONFIGURATION.md) | Prerequisites, Python 3.11 requirement, `.env` variables, step-by-step local setup |
| **09** | **Testing & Verification** | [09_TESTING_AND_VERIFICATION.md](09_TESTING_AND_VERIFICATION.md) | Multi-tier verification, executed vs unexecuted tests, unit tests, mock strategies |
| **10** | **Deployment & Security** | [10_DEPLOYMENT_AND_SECURITY.md](10_DEPLOYMENT_AND_SECURITY.md) | Docker containerization, security policies, path traversal defense, HIPAA/GDPR |
| **11** | **History & Roadmap** | [11_DEVELOPMENT_HISTORY_AND_ROADMAP.md](11_DEVELOPMENT_HISTORY_AND_ROADMAP.md) | Phases 1A–1G chronology, key technical decisions, known discrepancies, future phases |
| **12** | **Requirements Traceability**| [12_REQUIREMENTS_TRACEABILITY.md](12_REQUIREMENTS_TRACEABILITY.md) | 25-item requirements matrix mapped to source code, verification status, and evidence |
| 📋 | **Audit Report** | [DOCUMENTATION_AUDIT_REPORT.md](DOCUMENTATION_AUDIT_REPORT.md) | Auditor logs, verified files, uninspected files, resolved discrepancies, formal sign-off |
| 📑 | **Master Word Document** | [GAN_Based_Oral_Cancer_Detection_Platform_Technical_Documentation.docx](GAN_Based_Oral_Cancer_Detection_Platform_Technical_Documentation.docx) | Comprehensive compiled single-document report with formatting, tables, and TOC |

---

## 🧭 Role-Based Navigation Guide

- **Machine Learning Engineers:** Start with [03_AI_ML_TECHNICAL_DOCUMENTATION.md](03_AI_ML_TECHNICAL_DOCUMENTATION.md) and [06_DATABASE_AND_KNOWLEDGE_BASE.md](06_DATABASE_AND_KNOWLEDGE_BASE.md).
- **Backend Developers:** Review [04_BACKEND_DOCUMENTATION.md](04_BACKEND_DOCUMENTATION.md), [07_API_REFERENCE.md](07_API_REFERENCE.md), and [08_SETUP_AND_CONFIGURATION.md](08_SETUP_AND_CONFIGURATION.md).
- **Frontend Engineers:** Study [05_FRONTEND_DOCUMENTATION.md](05_FRONTEND_DOCUMENTATION.md) and [07_API_REFERENCE.md](07_API_REFERENCE.md).
- **Security & DevOps Engineers:** Inspect [10_DEPLOYMENT_AND_SECURITY.md](10_DEPLOYMENT_AND_SECURITY.md) and [08_SETUP_AND_CONFIGURATION.md](08_SETUP_AND_CONFIGURATION.md).
- **Auditors & Project Managers:** Consult [01_PROJECT_OVERVIEW.md](01_PROJECT_OVERVIEW.md), [12_REQUIREMENTS_TRACEABILITY.md](12_REQUIREMENTS_TRACEABILITY.md), and [DOCUMENTATION_AUDIT_REPORT.md](DOCUMENTATION_AUDIT_REPORT.md).

---

## ⚡ Quick System Summary

```
                      Oral Cancer Detection Platform Architecture
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                           FastAPI Multimodal Gateway                            │
  │                      (Asynchronous Orchestration Engine)                        │
  └────────┬──────────────────────┬───────────────────────┬─────────────────────────┘
           │                      │                       │
           ▼                      ▼                       ▼
  ┌──────────────────┐  ┌──────────────────┐    ┌──────────────────┐
  │  Vision & XAI    │  │  GraphRAG Index  │    │  Report Engine   │
  │  EfficientNetB0  │  │  FAISS (384-dim) │    │  Groq Cloud LLM  │
  │  4 CAM Variants  │  │  Neo4j AuraDB    │    │  (Llama-3.3-70B) │
  └──────────────────┘  └──────────────────┘    └──────────────────┘
```

- **Core Classifier:** `EfficientNetB0` (`models/best_efficientnetb0.keras`, 33.8 MB) fine-tuned for OSCC histopathology.
- **Calibrated Cut-off:** `0.850266` (Empirical F1-optimized threshold).
- **Verified Performance:** Accuracy **94.79%**, Precision **100.0%**, Sensitivity **89.56%**, ROC-AUC **0.9933**.
- **Attribution Algorithms:** Grad-CAM, Grad-CAM++, LayerCAM, and HiResCAM extracted from convolutional layer `top_conv`.
- **Literature Grounding:** FAISS `IndexFlatIP` containing 189 indexed chunks embedded via `all-MiniLM-L6-v2`.
- **Knowledge Graph:** Neo4j disease ontology and audit trail persistence.
- **Reporting:** Groq LLM API with bound clinical prompting and graceful template fallback.
