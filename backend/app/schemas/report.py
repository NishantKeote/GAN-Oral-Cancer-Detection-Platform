"""LLM report synthesis response schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class ReportErrorDetail(BaseModel):
    """Structured error payload when Groq report generation fails."""

    code: str = Field(..., description="Exception or error classification code")
    message: str = Field(..., description="Human-readable description of the failure")


class GroqReport(BaseModel):
    """Payload representing synthesized LLM research report or failure state."""

    status: str = Field(..., description="Report status ('ok' or 'error')")
    provider: str = Field(default="Groq", description="LLM inference provider")
    model: str = Field(..., description="Model identifier used for report synthesis")
    generated_at: str = Field(..., description="ISO 8601 UTC timestamp of report generation")
    text: Optional[str] = Field(default=None, description="Markdown report text if successful")
    error: Optional[ReportErrorDetail] = Field(default=None, description="Error detail if generation failed")
