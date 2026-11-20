# 10. Deployment & Security Documentation

## 1. Deployment Readiness Assessment

| Evaluation Dimension | Current State | Production Requirement | Gap / Status |
| :--- | :--- | :--- | :--- |
| **Architecture** | Modular FastAPI Application | Containerized Microservices | Local dev ready; containerization required |
| **Authentication / Authorization** | None (Public Intranet) | OAuth2 / JWT Bearer Tokens | **Gap:** Needs auth middleware for multi-user access |
| **Transport Security** | HTTP (Plaintext) | HTTPS / TLS 1.3 Termination | **Gap:** Requires Nginx/Traefik reverse proxy |
| **Containerization** | None (Host OS Python) | Docker / Docker Compose | **Blueprint Provided Below** |
| **Path Traversal Protection** | Regex Whitelist Sanitization | Strict Canonical Path Resolution | **Implemented & Verified** in `heatmaps.py` |
| **File Upload Validation** | Extension + Magic Bytes Check | Antivirus Scanning + Image Re-encoding | **Partially Implemented** |
| **Credential Management** | `.env` file + Pydantic Settings | Cloud KMS / Vault Secrets | **Implemented** for local; KMS needed for cloud |
| **Health Probes** | `GET /health` with component status | Kubernetes Liveness / Readiness Probes | **Implemented & Verified** |

> [!WARNING]
> ### Production Readiness Warning
> The current platform is suited for **Local Development and Research Evaluation**. It must not be deployed directly to public clinical networks without implementing SSL termination, user authentication, and rate limiting.

---

## 2. Docker Containerization Strategy

### 2.1 Multi-Stage Dockerfile Blueprint

```dockerfile
# ----------------------------------------------------
# Stage 1: Dependency Builder
# ----------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ----------------------------------------------------
# Stage 2: Runtime Production Image
# ----------------------------------------------------
FROM python:3.11-slim-bookworm AS runner

# Install OpenCV and C runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root system user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy repository models, knowledge base, and backend code
COPY --chown=appuser:appuser models/ /app/models/
COPY --chown=appuser:appuser knowledge_base/ /app/knowledge_base/
COPY --chown=appuser:appuser backend/ /app/backend/

# Create artifacts directory with write permissions
RUN mkdir -p /app/artifacts && chown -R appuser:appuser /app/artifacts

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### 2.2 Docker Compose Blueprint (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: oral_cancer_api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - DEBUG=False
      - NEO4J_URI=${NEO4J_URI}
      - NEO4J_USER=${NEO4J_USER}
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - artifacts_data:/app/artifacts
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  artifacts_data:
    driver: local
```

---

## 3. Security Architecture & Threat Mitigation

### 3.1 Input Validation & File Ingestion Security
- **MIME Type Sniffing:** Verifies file content headers against allowed image types (`image/jpeg`, `image/png`, `image/tiff`). Uploaded filenames are discarded and replaced with randomized server-side UUIDs to prevent file-extension spoofing.
- **Payload Size Clamping:** Enforces a hard 25 MB payload limit to prevent Memory Exhaustion / Denial of Service (DoS) attacks via decompression bombs.
- **EXIF / Metadata Stripping:** All uploaded histopathology tiles are transcoded into memory via `PIL.Image`, stripping patient identifying information (PII) embedded in EXIF or DICOM headers before saving or processing.

### 3.2 Path Traversal & File Artifact Protection
Heatmap retrieval in `backend/app/routers/heatmaps.py` is fortified against directory traversal attacks:
```python
# Whitelist enforcement against path traversal (../)
ALLOWED_FILENAMES = {
    "gradcam.png",
    "gradcam_plus_plus.png",
    "layercam.png",
    "hirescam.png"
}

if filename not in ALLOWED_FILENAMES:
    raise HTTPException(status_code=404, detail="Invalid heatmap artifact requested")

# Enforce strict regex on case_id
if not re.match(r"^CASE-[0-9a-fA-F-]+$", case_id):
    raise HTTPException(status_code=400, detail="Invalid case identifier")
```

### 3.3 Credential Protection & Secret Masking
- **Git Hygiene:** `.env` is permanently excluded via `.gitignore`.
- **Log Sanitization:** Sensitive credentials (`NEO4J_PASSWORD`, `GROQ_API_KEY`) are masked in telemetry endpoints and application logs (`gsk_...` $\to$ `gsk_***`).

---

## 4. Clinical Privacy & Regulatory Compliance (HIPAA / GDPR)

1. **De-Identification:** Patient IDs must be pseudorandom surrogate keys (e.g. `PAT-9942`) rather than government identifiers (SSN, National ID).
2. **Audit Logging:** Every classification event records timestamp, model version, and diagnostic outcome into the Neo4j knowledge graph, satisfying regulatory audit trail requirements for Clinical Decision Support Systems (CDSS).
3. **Data Retention:** Heatmap artifacts in `artifacts/{case_id}/` should be governed by a retention policy (e.g. automatic purge after 30 days unless archived by an authorized pathologist).
