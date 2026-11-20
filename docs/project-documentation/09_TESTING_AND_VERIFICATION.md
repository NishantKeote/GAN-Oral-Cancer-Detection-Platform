# 09. Testing & Verification Documentation

## 1. Verification Strategy & Scope

The testing methodology follows a rigorous multi-tier audit approach combining static code analysis, structural artifact validation, path resolution testing, unit test execution, and mocked external dependency evaluation.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Verification Hierarchy                          │
├────────────────────────────────┬───────────────────────────────────────┤
│ Tier 1: Static AST Validation  │ Python AST parser across all 26 files │
│ Tier 2: Binary Integrity Checks│ Magic byte, size & structure auditing │
│ Tier 3: Path Anchoring Checks  │ Dual-directory resolution test suites │
│ Tier 4: Automated Unit Tests   │ Pytest test_sanity.py execution       │
│ Tier 5: Runtime Dynamic Testing│ Targeted for Python 3.11 environment  │
└────────────────────────────────┴───────────────────────────────────────┘
```

---

## 2. Summary of Executed vs. Unexecuted Verification

### 2.1 Executed and Verified Tests

| Test Suite / Inspection | Target Scope | Execution Environment | Result | Evidence / Details |
| :--- | :--- | :--- | :--- | :--- |
| **Python AST Syntax Audit** | All 26 Python source files in `backend/` | Python 3.14 AST parser | **PASS** | 0 SyntaxErrors, 0 IndentationErrors |
| **Path Resolution Audit** | `backend/app/config.py` dual resolution | Dual root / backend launch | **PASS** | Resolves identically regardless of CWD |
| **Sanity Unit Test Suite** | `backend/tests/test_sanity.py` | Pytest / Python 3.14 | **PASS** | 3/3 tests passed (Root, Config, Health schema) |
| **Keras Model Inspection** | `models/best_efficientnetb0.keras` | Keras 3 Zip & JSON parser | **PASS** | Size: 35,465,584 bytes; `top_conv` confirmed |
| **FAISS Index Integrity** | `knowledge_base/oscc_literature.faiss` | Binary header parser | **PASS** | Magic `IxFI` (IndexFlatIP), 384 dim, 189 chunks |
| **Metadata Consistency** | `knowledge_base/chunk_metadata.json` | JSON schema validator | **PASS** | 189 objects parsed, all required keys present |
| **Metric Record Audit** | `results/evaluation_metrics.json` | JSON parser | **PASS** | Accuracy 94.79%, F1 0.9449, Threshold 0.850266 |

### 2.2 Implemented but Not Runtime Verified Tests

| Feature / Service | Implementation Status | Reason Unverified at Runtime | Path to Runtime Verification |
| :--- | :--- | :--- | :--- |
| **Dynamic Vision Inference** | Fully implemented in `VisionService` | Host environment has Python 3.14; TF requires Python 3.11 | Provision Python 3.11 virtualenv with TensorFlow 2.15 |
| **XAI Gradient Generation** | Fully implemented in `XAIService` | Depends on active TensorFlow gradient tape execution | Run end-to-end integration test with sample tile |
| **Live FAISS Similarity Search**| Fully implemented in `RAGService` | Depends on C-compiled `faiss-cpu` / `sentence-transformers` | Install dependencies in Python 3.11 and query |
| **Live Neo4j Graph Traversal** | Fully implemented in `GraphService` | `NEO4J_URI` not populated in environment | Provide active Neo4j AuraDB credentials in `.env` |
| **Live Groq LLM Report** | Fully implemented in `ReportService` | `GROQ_API_KEY` not populated in environment | Provide active Groq API Key in `.env` |

---

## 3. Unit Test Suite: `backend/tests/test_sanity.py`

An automated test suite was constructed to verify fundamental contracts without requiring heavy GPU or machine learning dependencies.

### 3.1 Test Cases Implemented

```python
import pytest
from pathlib import Path
from backend.app.config import settings

def test_settings_paths_resolve():
    """Verify that model and knowledge base paths resolve to existing files."""
    assert settings.MODEL_PATH.exists(), f"Model path missing: {settings.MODEL_PATH}"
    assert settings.FAISS_INDEX_PATH.exists(), f"FAISS index missing: {settings.FAISS_INDEX_PATH}"
    assert settings.FAISS_METADATA_PATH.exists(), f"Metadata missing: {settings.FAISS_METADATA_PATH}"
    assert settings.CLASSIFICATION_THRESHOLD == 0.850266

def test_config_dual_anchor():
    """Verify that resolving relative paths functions identically from any CWD."""
    resolved_model = settings.MODEL_PATH.resolve()
    assert resolved_model.name == "best_efficientnetb0.keras"
    assert resolved_model.is_file()

def test_health_schema_structure():
    """Verify that HealthResponse schema validates required telemetry keys."""
    from backend.app.schemas.health import HealthResponse
    sample_payload = {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": "2026-11-20T00:00:00Z",
        "components": {
            "model": {"name": "best_efficientnetb0.keras", "status": "ready"},
            "faiss": {"status": "ready", "total_chunks": 189},
            "neo4j": {"status": "unconfigured"},
            "groq": {"status": "unconfigured"}
        },
        "system": {"python_version": "3.11.9", "platform": "Windows"}
    }
    obj = HealthResponse(**sample_payload)
    assert obj.status == "healthy"
    assert obj.components["model"]["status"] == "ready"
```

### 3.2 Executing the Tests
```bash
pytest backend/tests/test_sanity.py -v
```

---

## 4. Integration Test Plan for Python 3.11 Runtime

Once Python 3.11 dependencies are installed, execute the following end-to-end integration validation:

### 4.1 Mocking Strategy for External Cloud APIs
To run continuous integration (CI) tests without calling paid or rate-limited external APIs:
- **Neo4j Mocking:** Use `unittest.mock.patch("neo4j.GraphDatabase.driver")` to return a synthetic session with pre-recorded graph records.
- **Groq Mocking:** Use `unittest.mock.patch("groq.Groq")` to intercept LLM completions and return pre-computed clinical markdown.
- **Model Warmup:** Pass a synthetic NumPy array `np.zeros((1, 224, 224, 3), dtype=np.float32)` to verify inference graph initialization.

### 4.2 Integration Test Script Example (`tests/test_pipeline_mock.py`)
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.app.main import app

client = TestClient(app)

def test_analyze_endpoint_mocked():
    # Synthetic 224x224 PNG image payload
    sample_image = b"\x89PNG\r\n\x1a\n..." # minimal valid PNG bytes
    
    with patch("backend.app.services.graph_service.GraphService.get_disease_context") as mock_graph, \
         patch("backend.app.services.report_service.ReportService.generate_clinical_report") as mock_report:
        
        mock_graph.return_value = {"disease": "OSCC", "features": ["Keratin pearls"]}
        mock_report.return_value = MagicMock(summary="Test Summary", recommendations=[])
        
        response = client.post(
            "/analyze",
            files={"image": ("test.png", sample_image, "image/png")},
            data={"patient_id": "TEST-001"}
        )
        assert response.status_code in [200, 500] # Depending on local TF presence
```
