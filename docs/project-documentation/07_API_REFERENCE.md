# 07. API Reference

## 1. Overview & Base Conventions

The Oral Cancer Detection API provides RESTful endpoints for real-time histopathology analysis, XAI heatmap artifact streaming, and system telemetry.

- **Base URL:** `http://localhost:8000`
- **Protocol:** HTTP/1.1 or HTTP/2
- **Data Exchange Format:** JSON (`application/json`) for metadata and responses; `multipart/form-data` for image ingestion.
- **Authentication:** Currently open for local/intranet development. (JWT / API Key authorization specified for production).
- **Interactive Documentation:**
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`

---

## 2. Endpoint Index

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | API root welcoming message, version, and links | No |
| `GET` | `/health` | System health check and component telemetry | No |
| `POST` | `/analyze` | Multi-modal diagnostic analysis and clinical report generation | No |
| `GET` | `/heatmaps/{case_id}/{filename}` | Stream generated XAI PNG heatmap overlay artifacts | No |

---

## 3. Detailed Endpoint Specifications

### 3.1 Root Endpoint: `GET /`

Returns API service metadata and documentation links.

#### Request
```http
GET / HTTP/1.1
Host: localhost:8000
```

#### Response: `200 OK`
```json
{
  "name": "Oral Cancer Detection API",
  "version": "1.0.0",
  "status": "online",
  "docs_url": "/docs",
  "health_url": "/health"
}
```

---

### 3.2 Health & Telemetry: `GET /health`

Queries internal components (vision model, vector database, graph database, LLM provider) and returns aggregated operational readiness.

#### Request
```http
GET /health HTTP/1.1
Host: localhost:8000
```

#### Response: `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-11-20T12:00:00.000000Z",
  "components": {
    "model": {
      "name": "best_efficientnetb0.keras",
      "status": "ready",
      "path": "models/best_efficientnetb0.keras",
      "size_bytes": 35465584
    },
    "faiss": {
      "status": "ready",
      "index_path": "knowledge_base/oscc_literature.faiss",
      "total_chunks": 189
    },
    "neo4j": {
      "status": "unconfigured",
      "uri": ""
    },
    "groq": {
      "status": "unconfigured",
      "model": "llama-3.3-70b-versatile"
    }
  },
  "system": {
    "python_version": "3.11.9",
    "platform": "Windows-10-10.0.19045-SP0"
  }
}
```

---

### 3.3 Multimodal Analysis: `POST /analyze`

Executes the end-to-end inference pipeline: EfficientNetB0 classification, 4-method XAI generation, FAISS literature retrieval, Neo4j traversal, and Groq report synthesis.

#### Request Headers
```http
POST /analyze HTTP/1.1
Host: localhost:8000
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW
```

#### Request Form Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `image` | `UploadFile` (Binary) | **Yes** | Histopathology image file (JPEG, PNG, TIFF). Target: 224x224 RGB. |
| `patient_id` | `string` | **Yes** | Anonymized patient/case identifier (e.g., `"P-2026-0891"`). |
| `patient_name` | `string` | No | Optional patient name for reporting. |
| `patient_age` | `integer` | No | Patient age in years ($0 \le \text{age} \le 120$). |
| `patient_gender` | `string` | No | Biological sex (`"male"`, `"female"`, `"other"`). |
| `clinical_notes` | `string` | No | Clinician observations (e.g., `"Ulcerative lesion on lateral tongue border"`). |

#### Example cURL Command
```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "image=@tests/sample_tiles/oscc_tile_01.png" \
  -F "patient_id=PAT-9942" \
  -F "patient_age=58" \
  -F "patient_gender=male" \
  -F "clinical_notes=Persistent leukoplakia with ulceration on left lateral border of tongue, 6 months history."
```

#### Response: `200 OK`
```json
{
  "case_id": "CASE-4f81c9a2-92df-4822-b520-2f3b9c086d4e",
  "patient_id": "PAT-9942",
  "timestamp": "2026-11-20T12:00:15.342100Z",
  "prediction": {
    "predicted_class": "Oral Squamous Cell Carcinoma (OSCC)",
    "probability": 0.98412,
    "confidence": 0.98412,
    "threshold_applied": 0.850266,
    "raw_logit": 4.127
  },
  "heatmaps": {
    "gradcam": "/heatmaps/CASE-4f81c9a2-92df-4822-b520-2f3b9c086d4e/gradcam.png",
    "gradcam_plus_plus": "/heatmaps/CASE-4f81c9a2-92df-4822-b520-2f3b9c086d4e/gradcam_plus_plus.png",
    "layercam": "/heatmaps/CASE-4f81c9a2-92df-4822-b520-2f3b9c086d4e/layercam.png",
    "hirescam": "/heatmaps/CASE-4f81c9a2-92df-4822-b520-2f3b9c086d4e/hirescam.png"
  },
  "literature_evidence": [
    {
      "chunk_id": "chunk_0042",
      "paper_id": "PMC_7482910",
      "title": "Histopathological grading and deep learning classification of Oral Squamous Cell Carcinoma",
      "authors": "Patel, R., Sharma, A., Kumar, S.",
      "year": 2021,
      "source_url": "https://doi.org/10.1016/j.oraloncology.2021.105230",
      "similarity_score": 0.8924,
      "text": "Keratin pearl formation and individual cell keratinization are defining hallmarks of well-differentiated oral squamous cell carcinoma. Dyskeratosis and mitotic figures further delineate invasion depth into the subepithelial connective tissue."
    }
  ],
  "graph_context": {
    "disease": "Oral Squamous Cell Carcinoma",
    "icd10": "C06.9",
    "risk_factors": ["Tobacco use", "Areca nut chewing", "Alcohol abuse", "HPV-16"],
    "diagnostic_features": ["Keratin pearls", "Cellular pleomorphism", "Nuclear hyperchromatism"]
  },
  "clinical_report": {
    "summary": "Automated evaluation of submitted biopsy tile demonstrates high likelihood of Oral Squamous Cell Carcinoma.",
    "diagnostic_impression": "Malignant histopathological features identified with 98.41% model confidence exceeding decision boundary (0.850266).",
    "xai_findings": "Attribution focuses intensely on atypical cellular clusters and dyskeratotic epithelial nests located in the central and lower quadrant of the patch.",
    "literature_correlation": "Findings align with Patel et al. (2021) regarding invasive epithelial island morphology.",
    "recommendations": [
      "Immediate expert histopathologic confirmation by a board-certified pathologist.",
      "Whole-slide immunohistochemistry (p16, Ki-67) to determine HPV status and proliferation index.",
      "Clinical staging and head/neck contrast-enhanced CT/MRI examination."
    ]
  },
  "status": "completed"
}
```

---

### 3.4 Heatmap Artifact Retrieval: `GET /heatmaps/{case_id}/{filename}`

Streams a generated Explainable AI attribution PNG image for a specific case.

#### Path Parameters
- `case_id`: Alphanumeric UUID case identifier (`CASE-[a-zA-Z0-9-]+`).
- `filename`: Restricted strictly to:
  - `gradcam.png`
  - `gradcam_plus_plus.png`
  - `layercam.png`
  - `hirescam.png`

#### Request
```http
GET /heatmaps/CASE-4f81c9a2-92df-4822-b520-2f3b9c086d4e/gradcam.png HTTP/1.1
Host: localhost:8000
```

#### Response: `200 OK`
- **Content-Type:** `image/png`
- **Content-Length:** ~120 KB
- **Body:** Raw binary image stream.

---

## 4. Error Responses & Status Codes

| HTTP Code | Condition | JSON Response Body |
| :--- | :--- | :--- |
| `400 Bad Request` | Unsupported file MIME type or unreadable image stream | `{"detail": "Uploaded file is not a valid image (JPEG/PNG/TIFF expected)."}` |
| `404 Not Found` | Requested case or heatmap file does not exist | `{"detail": "Heatmap artifact not found for specified case."}` |
| `422 Unprocessable`| Missing required multipart form field (e.g., missing `image`) | Standard FastAPI validation error object |
| `500 Internal Error`| Model failure or unhandled internal exception | `{"detail": "Analysis pipeline failure: <internal error message>"}` |
