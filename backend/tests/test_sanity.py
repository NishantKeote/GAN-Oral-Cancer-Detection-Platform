"""Sanity test verifying configuration defaults, directory structures, and service modules."""

from pathlib import Path


def test_directory_structure():
    """Verify backend structure conforms to Phase 1G blueprint."""
    backend_root = Path(__file__).parent.parent
    assert (backend_root / "app").is_dir()
    assert (backend_root / "app" / "core").is_dir()
    assert (backend_root / "app" / "routers").is_dir()
    assert (backend_root / "app" / "services").is_dir()
    assert (backend_root / "app" / "schemas").is_dir()
    assert (backend_root / "artifacts").is_dir()
    assert (backend_root / "requirements.txt").is_file()
    assert (backend_root / ".env.example").is_file()


def test_service_modules():
    """Verify all six core services are implemented in services/."""
    services_dir = Path(__file__).parent.parent / "app" / "services"
    expected_services = [
        "vision_service.py",
        "xai_service.py",
        "rag_service.py",
        "graph_service.py",
        "report_service.py",
        "analysis_service.py",
    ]
    for svc in expected_services:
        assert (services_dir / svc).is_file(), f"Missing service file: {svc}"


def test_model_and_index_resources():
    """Verify model weights and FAISS knowledge base files exist."""
    project_root = Path(__file__).parent.parent.parent
    assert (project_root / "models" / "best_efficientnetb0.keras").is_file()
    assert (project_root / "knowledge_base" / "oscc_literature.faiss").is_file()
    assert (project_root / "knowledge_base" / "chunk_metadata.json").is_file()


def test_requirements_file():
    """Verify requirements.txt contains critical dependencies."""
    backend_root = Path(__file__).parent.parent
    req_text = (backend_root / "requirements.txt").read_text(encoding="utf-8")
    assert "fastapi" in req_text
    assert "tensorflow" in req_text
    assert "faiss-cpu" in req_text
    assert "neo4j" in req_text
    assert "groq" in req_text
