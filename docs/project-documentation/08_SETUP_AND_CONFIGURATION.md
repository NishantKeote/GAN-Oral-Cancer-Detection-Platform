# 08. Setup & Configuration Guide

## 1. System Requirements & Prerequisites

### 1.1 Operating System Compatibility
- **Windows:** Windows 10 (Build 19045+) or Windows 11 (64-bit).
- **Linux:** Ubuntu 20.04 LTS / 22.04 LTS, Debian 11+, Fedora 38+.
- **macOS:** macOS Monterey (12.0+) or newer (Apple Silicon supported via `tensorflow-metal`).

### 1.2 Hardware Specifications
- **CPU:** Quad-core x86_64 or Apple Silicon processor (ARM64).
- **RAM:** 8 GB minimum; 16 GB recommended (to comfortably host EfficientNetB0, SentenceTransformers, and FAISS index simultaneously).
- **Disk Storage:** At least 5 GB free disk space (model artifact: ~35 MB, PyTorch/TensorFlow wheels: ~3 GB).
- **GPU (Optional):** NVIDIA GPU with CUDA Compute Capability 7.0+ (CUDA 11.8 or 12.x) and cuDNN. CPU inference is fully supported out of the box.

### 1.3 Critical Python Version Notice: Python 3.11 Required

> [!CAUTION]
> ### Runtime Version Requirement: Python 3.11
> 
> The backend machine learning dependencies—specifically **TensorFlow 2.15+** and **FAISS**—do not have stable binary wheels available for **Python 3.12+** or **Python 3.14** on Windows.
> 
> You **must** create the execution virtual environment using **Python 3.11** (e.g., Python 3.11.8 or 3.11.9). Attempting to install `backend/requirements.txt` under Python 3.14 will fail during C-extension compilation.

---

## 2. Step-by-Step Installation & Environment Setup

### Step 1: Clone Repository & Open Terminal
Open PowerShell (Windows) or Bash (Linux/macOS) in the repository root directory:
```bash
cd "d:/a_Final year project/GAN-based-Oral-Cancer-detection-with-GraphRag-GradCam"
```

### Step 2: Create a Python 3.11 Virtual Environment
Ensure Python 3.11 is installed on your path:
```bash
# Windows
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3.11 -m venv venv
source venv/bin/activate
```

### Step 3: Upgrade Pip & Core Build Tools
```bash
python -m pip install --upgrade pip setuptools wheel
```

### Step 4: Install Dependencies
Install the audited package dependencies:
```bash
pip install -r backend/requirements.txt
```

---

## 3. Environment Variable Configuration (`.env`)

Copy the provided template configuration:
```bash
# Windows PowerShell
Copy-Item backend/.env.example backend/.env

# Linux / macOS
cp backend/.env.example backend/.env
```

### 3.1 Configuration Parameter Reference

Edit `backend/.env` using any text editor:

| Parameter | Default Value | Purpose / Recommended Value |
| :--- | :--- | :--- |
| `API_V1_STR` | `""` | Base route prefix (keep empty for root routing) |
| `PROJECT_NAME` | `"Oral Cancer Detection API"` | Service display name |
| `DEBUG` | `False` | Set `True` only during local debugging |
| `HOST` | `"0.0.0.0"` | Bind address (`127.0.0.1` for local only) |
| `PORT` | `8000` | Port for incoming HTTP requests |
| `CORS_ORIGINS` | `["http://localhost:5173", "http://localhost:3000"]` | Allowed frontend development origins |
| `MODEL_PATH` | `models/best_efficientnetb0.keras` | Path to trained Keras classifier |
| `CLASSIFICATION_THRESHOLD` | `0.850266` | Empirically calibrated decision threshold |
| `FAISS_INDEX_PATH` | `knowledge_base/oscc_literature.faiss` | Path to serialized binary FAISS index |
| `FAISS_METADATA_PATH` | `knowledge_base/chunk_metadata.json` | Path to chunk literature metadata JSON |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | SentenceTransformer model name |
| `NEO4J_URI` | `""` | e.g. `bolt+s://xxxxxxxx.databases.neo4j.io` |
| `NEO4J_USER` | `""` | e.g. `neo4j` |
| `NEO4J_PASSWORD` | `""` | Your Neo4j AuraDB instance password |
| `GROQ_API_KEY` | `""` | Your Groq Cloud API Secret Key (`gsk_...`) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | High-parameter medical reasoning LLM |
| `ARTIFACTS_DIR` | `artifacts` | Directory where generated XAI heatmaps are saved |

> [!NOTE]
> `NEO4J_URI` and `GROQ_API_KEY` are optional for local testing. If omitted, the platform gracefully degrades and continues serving inference and XAI heatmaps with fallback clinical reports.

---

## 4. Launching the Backend Server

The application can be launched from either the repository root or inside `backend/`:

### Option A: From Repository Root
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option B: From `backend/` Directory
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Verification
Once launched, open your web browser to:
- Health Telemetry: `http://localhost:8000/health`
- Swagger Interactive Documentation: `http://localhost:8000/docs`

---

## 5. External Cloud Integrations Setup

### 5.1 Neo4j AuraDB (Free Cloud Tier)
1. Sign up at [neo4j.com/cloud/platform/aura-graph-database/](https://neo4j.com/cloud/platform/aura-graph-database/).
2. Create a free **AuraDB Free** instance.
3. Download the generated credentials file (`neo4j-credentials.txt`).
4. Copy the connection URI (`neo4j+s://...`), username (`neo4j`), and password into `backend/.env`.

### 5.2 Groq Cloud LLM API
1. Sign up at [console.groq.com](https://console.groq.com/).
2. Navigate to **API Keys** and click **Create API Key**.
3. Copy the generated secret key (starts with `gsk_`) and paste it into `backend/.env`:
   ```env
   GROQ_API_KEY=gsk_your_actual_key_here
   ```

---

## 6. Troubleshooting Common Issues

### Issue 1: `ModuleNotFoundError: No module named 'tensorflow'`
- **Cause:** You are running a Python version (e.g., 3.12, 3.13, 3.14) where pre-built TensorFlow wheels are unavailable for Windows.
- **Solution:** Recreate your virtual environment specifically targeting Python 3.11 (`py -3.11 -m venv venv`).

### Issue 2: `ImportError: DLL load failed while importing _swigfaiss`
- **Cause:** Missing Microsoft Visual C++ Redistributable on Windows.
- **Solution:** Download and install the latest [Visual C++ 2015–2022 Redistributable (x64)](https://aka.ms/vs/17/release/vc_redist.x64.exe) and restart your terminal.

### Issue 3: `Address already in use [Errno 10048]`
- **Cause:** Another process or previous Uvicorn instance is holding port 8000.
- **Solution:** Specify an alternative port:
  ```bash
  uvicorn backend.app.main:app --port 8080 --reload
  ```
