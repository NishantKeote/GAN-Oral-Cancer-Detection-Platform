# 02. Resource & Artifact Inventory

**Project:** GAN-based Oral Cancer Detection with GraphRAG and Grad-CAM  
**Audit Date:** November 2026  
**Auditor:** Antigravity AI  

---

## 1. Machine Learning & Deep Learning Artifacts

### 1.1. Model Checkpoints (`models/`)

The repository includes two trained TensorFlow / Keras 3 model archive files:

#### A. `models/best_efficientnetb0.keras` (Primary Production Model)
- **Size:** 35,387,305 bytes (~33.75 MB)
- **Keras Format:** Keras 3 Functional Model (`zip` archive containing `config.json`, `metadata.json`, and `model.weights.h5`)
- **Keras Version:** `3.13.2` (Saved on `2026-11-13@03:52:50`)
- **Input Shape:** `(None, 224, 224, 3)` with float32 values
- **Output Shape:** `(None, 1)` with sigmoid activation (continuous probability score)
- **Internal Layer Hierarchy:**
  1. `InputLayer` (`input_layer_1`, shape: `[None, 224, 224, 3]`)
  2. `Sequential` (`sequential`: RandomFlip, RandomRotation `0.04`, RandomZoom/Contrast `0.08`)
  3. `Functional` (`efficientnetb0`: backbone with top conv output shape `(None, 7, 7, 1280)`)
  4. `GlobalAveragePooling2D` (`global_average_pooling2d`)
  5. `BatchNormalization` (`batch_normalization`)
  6. `Dropout` (`dropout`, rate: `0.35`)
  7. `Dense` (`dense`, units: `128`, activation: `relu`)
  8. `Dropout` (`dropout_1`, rate: `0.25`)
  9. `Dense` (`dense_1`, units: `1`, activation: `sigmoid`)
- **Training Strategy:** Two-stage transfer learning:
  - Stage 1: Frozen EfficientNetB0 backbone, trained classification head (1253s duration).
  - Stage 2: Fine-tuned upper 40 layers of EfficientNetB0 with BatchNorm layers kept frozen (1041s duration, learning rate `1e-5`).
- **Optimal Decision Threshold:** `0.850266` (derived to balance sensitivity and specificity on validation split).
- **Class Mapping:** `{0: "Normal", 1: "OSCC"}` (Label is "OSCC" if sigmoid score $\ge 0.850266$, else "Normal").

#### B. `models/baseline_efficientnetb0.keras` (Baseline Experiment Model)
- **Size:** 19,081,701 bytes (~18.20 MB)
- **Keras Version:** `3.13.2` (Saved on `2026-11-13@03:33:18`)
- **Status:** Head-only frozen backbone checkpoint preceding fine-tuning.

---

## 2. Knowledge Base & Vector Index Artifacts (`knowledge_base/`)

### 2.1. Vector Database: `knowledge_base/oscc_literature.faiss`
- **File Size:** 290,349 bytes (~284 KB)
- **Vector Index Type:** Flat L2 / Inner Product FAISS Index
- **Total Vectors:** `189` vectors
- **Vector Dimensionality:** `384` dimensions
- **Embedding Model Required:** `sentence-transformers/all-MiniLM-L6-v2`
- **Search Strategy:** Query text is normalized, encoded to `(1, 384)` float32 vector, and queried with top-k=5 nearest-neighbor search.

### 2.2. Metadata Store: `knowledge_base/chunk_metadata.json`
- **File Size:** 345,784 bytes (~338 KB)
- **Total Chunks:** `189` records
- **Chunk Schema:**
  ```json
  {
    "chunk_id": "PMC8631280_chunk_0000",
    "paper_id": "PMC8631280",
    "year": 2021,
    "title": "The Impact of Histopathological Features on the Prognosis of Oral Squamous Cell Carcinoma: A Comprehensive Review and Meta-Analysis",
    "authors": "Dolens et al.",
    "source_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8631280/",
    "chunk_index": 0,
    "text": "Full text snippet of literature review..."
  }
  ```
- **Coverage:** Peer-reviewed PubMed Central (PMC) literature focusing on OSCC histopathological criteria, keratinization, nuclear pleomorphism, depth of invasion, and surgical margins.

---

## 3. Evaluation & Experimental Results (`results/`)

| File | Metric / Content Summary | Key Values |
|---|---|---|
| `test_metrics.json` | Final test evaluation metrics on held-out test split | Accuracy: `94.79%`, Precision: `100%`, Sensitivity: `89.56%`, Specificity: `100%`, F1: `0.9449`, ROC-AUC: `0.9933`, PR-AUC: `0.9942`, False Positive Rate: `0.0%`, False Negative Rate: `10.44%`, Threshold: `0.850266` |
| `classification_report.txt` | Per-class performance on 768 test images | Normal (support: 385): Precision 0.91, Recall 1.00, F1 0.95<br>OSCC (support: 383): Precision 1.00, Recall 0.90, F1 0.94 |
| `experiment_comparison.csv` | Head-only vs fine-tuned stages | E0-head Val Acc: 96.56%, Val F1: 0.9661<br>E1-finetune Val Acc: 97.48%, Val F1: 0.9752 |
| `training_history.csv` | Epoch-level history | Loss and categorical metrics over both training phases |
| Visual Plots (`.png`) | Confusion Matrix, ROC curve, PR curve, Dataset audit, Image samples, Training history | High-resolution publication plots confirming model training reproducibility |

---

## 4. Dependencies & Software Requirements

Extracted from notebook dependencies across all three notebooks:

### Core Python Dependencies:
- **Python Version:** 3.10+ (tested with Python 3.10 – 3.12; Note: TensorFlow does not yet support Python 3.14)
- **Deep Learning:** `tensorflow>=2.16.0` (or `keras>=3.13.0`)
- **Numerical & Image:** `numpy>=1.26.0`, `pillow>=10.0.0`, `opencv-python>=4.9.0`
- **Vector Retrieval:** `faiss-cpu>=1.8.0`, `sentence-transformers>=2.6.0`
- **Graph Database Driver:** `neo4j>=5.18.0`
- **LLM SDK:** `groq>=0.9.0`
- **API Server:** `fastapi>=0.111.0`, `uvicorn>=0.30.0`, `python-multipart>=0.0.9`, `pydantic>=2.7.0`
- **Data & Evaluation:** `pandas>=2.2.0`, `scikit-learn>=1.4.0`, `imagehash>=4.3.1`

---

## 5. Inventory of Missing & External Resources

### 5.1. Missing Files (Must Be Created):
1. **`requirements.txt` / virtual environment lockfile**: Currently nonexistent.
2. **Standalone Backend Application (`backend/`)**: Needs modular architecture containing `main.py`, config loaders, routers, services for CNN/XAI/FAISS/Neo4j/Groq.
3. **Frontend Application (`frontend/`)**: Modern React + TypeScript + Vite project.
4. **Neo4j Seeding Script / Graph Schema**: No script currently exists to initialize disease nodes and literature relationships.
5. **Environment Configuration File (`.env.example`)**: For documenting required credentials.

### 5.2. Missing Model Artifacts:
- **CycleGAN / WGAN / HistoGAN:** Completely absent from repository.

### 5.3. External Services & Credentials Required for Runtime:
- **Groq API Key:** Required for `groq_client.chat.completions.create`.
- **Neo4j Database Instance:** Active URI, database name, username, and password (e.g., Neo4j Aura or local Docker instance).
- **Hugging Face Hub Access:** To download `sentence-transformers/all-MiniLM-L6-v2` on first run.
