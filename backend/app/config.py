"""Application configuration module using Pydantic Settings.

Reads environment variables from system environment and optional .env file.
Provides type-safe configuration values with reasonable defaults for development.
"""

from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory anchors (stable regardless of execution working directory)
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Central configuration settings for the OSCC Backend application."""

    # Environment & Server
    ENV: str = Field(default="development", description="Runtime environment (development, production, testing)")
    DEBUG: bool = Field(default=True, description="Enable debug mode and detailed logs")
    HOST: str = Field(default="0.0.0.0", description="Host address to bind the Uvicorn server")
    PORT: int = Field(default=8000, description="Port number to bind the Uvicorn server")

    # CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins for the frontend",
    )

    # ML Model & Knowledge Base Artifact Paths (Anchored to Project Root)
    MODEL_PATH: Path = Field(
        default_factory=lambda: PROJECT_ROOT / "models" / "best_efficientnetb0.keras",
        description="Path to trained EfficientNetB0 Keras model file",
    )
    FAISS_PATH: Path = Field(
        default_factory=lambda: PROJECT_ROOT / "knowledge_base" / "oscc_literature.faiss",
        description="Path to FAISS vector index file",
    )
    METADATA_PATH: Path = Field(
        default_factory=lambda: PROJECT_ROOT / "knowledge_base" / "chunk_metadata.json",
        description="Path to literature chunk metadata JSON file",
    )
    ARTIFACT_DIR: Path = Field(
        default_factory=lambda: BACKEND_DIR / "artifacts",
        description="Directory to store generated XAI heatmaps and overlays",
    )

    # Inference & Constraints
    CLASSIFICATION_THRESHOLD: float = Field(
        default=0.850266,
        description="Sigmoid score cutoff threshold for OSCC vs Normal classification",
    )
    MAX_UPLOAD_BYTES: int = Field(
        default=20 * 1024 * 1024,  # 20 MB
        description="Maximum allowed image upload size in bytes",
    )

    # Neo4j Graph Database
    NEO4J_URI: str = Field(default="", description="Neo4j connection URI (bolt:// or neo4j+s://)")
    NEO4J_USERNAME: str = Field(default="neo4j", description="Neo4j username")
    NEO4J_PASSWORD: str = Field(default="", description="Neo4j password")
    NEO4J_DATABASE: str = Field(default="neo4j", description="Target Neo4j database name")

    # Groq LLM API
    GROQ_API_KEY: str = Field(default="", description="Groq API key for report generation")
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile", description="Target Groq model identifier")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        """Parse comma-separated strings into a list of origin strings."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("MODEL_PATH", "FAISS_PATH", "METADATA_PATH", "ARTIFACT_DIR", mode="after")
    @classmethod
    def resolve_paths(cls, value: Path) -> Path:
        """Resolve path to a stable project-relative absolute path.

        Handles execution from either the repository root or backend working directory,
        while strictly preserving user environment variable overrides.
        """
        if not value:
            return value

        # If already absolute, return normalized absolute path
        if value.is_absolute():
            return value.resolve()

        # Check if relative to BACKEND_DIR (e.g. "../models/...", "./artifacts")
        candidate_backend = (BACKEND_DIR / value).resolve()
        if candidate_backend.exists():
            return candidate_backend

        # Check if relative to PROJECT_ROOT (e.g. "models/...", "knowledge_base/...")
        candidate_root = (PROJECT_ROOT / value).resolve()
        if candidate_root.exists():
            return candidate_root

        # If path does not exist yet (e.g. artifacts directory before creation),
        # anchor artifacts to BACKEND_DIR and others to candidate_backend
        if "artifact" in str(value).lower():
            return candidate_backend

        return candidate_backend


# Singleton instance for application-wide import
settings = Settings()
