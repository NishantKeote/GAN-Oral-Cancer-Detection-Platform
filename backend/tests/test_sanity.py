"""Sanity test verifying configuration defaults and directory structures."""

from pathlib import Path


def test_directory_structure():
    """Verify backend structure conforms to Phase 1A blueprint."""
    backend_root = Path(__file__).parent.parent
    assert (backend_root / "app").is_dir()
    assert (backend_root / "app" / "core").is_dir()
    assert (backend_root / "app" / "routers").is_dir()
    assert (backend_root / "app" / "services").is_dir()
    assert (backend_root / "app" / "schemas").is_dir()
    assert (backend_root / "artifacts").is_dir()
    assert (backend_root / "requirements.txt").is_file()
    assert (backend_root / ".env.example").is_file()


def test_requirements_file():
    """Verify requirements.txt contains critical dependencies."""
    backend_root = Path(__file__).parent.parent
    req_text = (backend_root / "requirements.txt").read_text(encoding="utf-8")
    assert "fastapi" in req_text
    assert "tensorflow" in req_text
    assert "faiss-cpu" in req_text
    assert "neo4j" in req_text
    assert "groq" in req_text
