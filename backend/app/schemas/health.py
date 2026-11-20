"""Health check response schemas."""

from typing import Dict, List
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for GET /health endpoint."""

    status: str = Field(..., description="Overall backend health status")
    phase: str = Field(..., description="Current development phase")
    model: str = Field(default="EfficientNetB0", description="Target CNN classifier architecture")
    threshold: float = Field(..., description="Classification decision threshold")
    xai_methods: List[str] = Field(..., description="Supported Explainable AI attribution methods")
    services: Dict[str, bool] = Field(default_factory=dict, description="Component readiness flags")
    version: str = Field(default="2.0.0", description="API version")
