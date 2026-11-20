# 01. Repository Audit Report

**Project:** GAN-based Oral Cancer Detection with GraphRAG and Grad-CAM  
**Audit Date:** November 2026  
**Auditor:** Antigravity AI  
**Repository Branch:** `main` (commit `90fabd4`)

---

## 1. Executive Summary

This repository represents an academic major project aimed at multimodal oral cancer detection (specifically Oral Squamous Cell Carcinoma - OSCC) combining deep learning computer vision, explainable artificial intelligence (XAI), vector search, graph database knowledge representation, and Large Language Model (LLM) report generation.

While the project demonstrates a sophisticated concept and includes trained model weights and vector literature indices, **the codebase currently exists entirely as Jupyter Notebooks**. There are **no standalone Python files (`.py`)**, **no backend server entrypoint**, **no package manifest (`requirements.txt` / `pyproject.toml`)**, and **no frontend application codebase**. Furthermore, the repository contains **no code or model artifacts for Generative Adversarial Networks (CycleGAN / WGAN / HistoGAN)** despite the title and claims in `README.md`.

---

## 2. Git & Version Control Audit

- **Current Branch:** `main`
- **Working Tree:** Clean (no uncommitted changes)
- **Commit History Summary:**
  1. `90fabd4`: Add comprehensive README for GAN-based oral cancer detection
  2. `6b218bf`: Added Knowledge base data
  3. `46ab406`: Add files via upload
  4. `70d2fb6`: ADDED XAI FEATURE
  5. `6c16f18`: Merge remote repository with oral cancer project

All tracked files were committed via bulk uploads and merges without CI/CD workflows, unit tests, or environment configurations.

---

## 3. Complete File & Directory Inventory

The repository contains exactly **18 files** across **4 subdirectories**:

| Directory | File Name | Size (Bytes / MB) | Type / Purpose |
|---|---|---|---|
| `/` | `README.md` | 10,270 B | Project documentation & methodology overview |
| `knowledge_base/` | `chunk_metadata.json` | 345,784 B (338 KB) | 189 literature chunks with PMC IDs, titles, and text snippets |
| `knowledge_base/` | `oscc_literature.faiss` | 290,349 B (284 KB) | Precomputed FAISS vector index (384-dimensional embeddings) |
| `models/` | `baseline_efficientnetb0.keras` | 19,081,701 B (18.2 MB) | Keras 3 Functional Model (Head-only frozen baseline) |
| `models/` | `best_efficientnetb0.keras` | 35,387,305 B (33.8 MB) | Keras 3 Functional Model (Fine-tuned top 40 layers, best checkpoint) |
| `notebooks/` | `oral_cancer_detection_EfficientNet_V2.ipynb` | 2,360,805 B (2.25 MB) | Training pipeline on Kaggle OSCC dataset |
| `notebooks/` | `oscc_efficientnetb0_xai_four_methods.ipynb` | 1,513,670 B (1.44 MB) | 4-method XAI benchmarking and faithfulness validation |
| `notebooks/` | `OSCC_Integrated_GraphRAG_EfficientNet_XAI_FINAL_FIXED.ipynb` | 219,216 B (214 KB) | Integrated Colab notebook hosting FastAPI + HTML UI |
| `results/` | `classification_report.txt` | 666 B | Test set precision, recall, f1-score, and test metrics |
| `results/` | `confusion_matrix.png` | 29,231 B | Evaluation confusion matrix plot |
| `results/` | `dataset_audit.png` | 50,113 B | Kaggle dataset class balance and split audit plot |
| `results/` | `experiment_comparison.csv` | 700 B | Comparison between frozen head and fine-tuned experiments |
| `results/` | `image_samples.png` | 3,359,544 B (3.2 MB) | Dataset sample histopathology tiles |
| `results/` | `precision_recall_curve.png` | 23,754 B | Precision-recall curve evaluation plot |
| `results/` | `roc_curve.png` | 34,431 B | ROC-AUC evaluation plot |
| `results/` | `test_metrics.json` | 330 B | JSON dump of optimal threshold and test metrics |
| `results/` | `training_history.csv` | 6,567 B | Epoch-by-epoch loss and accuracy metrics |
| `results/` | `training_history.png` | 70,493 B | Loss and accuracy training curves plot |

---

## 4. Key Discrepancies & Gap Analysis

### 4.1. Generative Adversarial Networks (CycleGAN / WGAN / HistoGAN)
- **Claimed in README:** Section 1 describes CycleGAN synthetic image generation with 100 training epochs, MAE 0.0918, and identity loss 0.0600.
- **Audit Finding:** **0 GAN files exist.** There are no GAN architecture definitions, training notebooks, generator/discriminator weight checkpoints (`.keras`/`.pt`), or generated synthetic image folders in the repository. The classifier was trained strictly on real Kaggle histopathological images using standard affine augmentations (flip, zoom, rotation).

### 4.2. Backend Implementation
- **Claimed in README:** Getting Started hints at running backend modules and API servers.
- **Audit Finding:** The backend exists exclusively inside cells 1–13 of `OSCC_Integrated_GraphRAG_EfficientNet_XAI_FINAL_FIXED.ipynb`. It is tightly coupled to Google Colab environments (`google.colab.drive`, `google.colab.userdata`, `pyngrok`, and Colab hardcoded paths like `/content/drive/MyDrive/...`). It cannot be run locally without code extraction and refactoring.

### 4.3. Dependency Management
- **Audit Finding:** There is **no `requirements.txt`**, `Pipfile`, `environment.yml`, or `pyproject.toml`. Dependencies must be reverse-engineered from notebook `!pip install` statements.

### 4.4. Missing Neo4j Seed Scripts
- **Audit Finding:** The notebook queries an existing Neo4j instance expecting pre-populated `(:Disease {name: "Oral Squamous Cell Carcinoma"})` and connected graph entities. No schema definition, Cypher seed queries, or export dumps exist in the repository.

### 4.5. Frontend Application
- **Audit Finding:** The only frontend is a raw HTML/CSS/JS string (24.5 KB) embedded inside Python variable `HTML_PAGE` in the integrated notebook, served directly via FastAPI's `HTMLResponse`. There is no modern web frontend framework (no React, no TypeScript, no Vite).

---

## 5. Summary of System Maturity

| Component | Maturity Level | Readiness |
|---|---|---|
| EfficientNetB0 Classifier | **Complete** | Production-ready Keras 3 weights (`models/best_efficientnetb0.keras`) |
| XAI Attribution Engine | **Complete** | Fully validated math for 4 methods; needs extraction from notebook |
| FAISS Literature Index | **Complete** | Local index (`.faiss`) and metadata (`.json`) ready for semantic search |
| Neo4j Graph Database | **Partially Implemented** | Cypher queries written; requires live database instance or seed data |
| Groq LLM Integration | **Complete** | Grounded prompting and guardrails implemented; requires API key |
| CycleGAN Image Generation | **Missing** | Not implemented in repository |
| Standalone Backend API | **Missing** | Code exists inside Colab notebook; needs extraction to modular FastAPI |
| Modern Web Frontend | **Missing** | Needs full greenfield implementation with React + TypeScript + Vite |
