"""Explainable AI (XAI) attribution response schemas."""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class XAIMethodStats(BaseModel):
    """Statistical summary metrics for a normalized attribution heatmap."""

    min: float = Field(default=0.0, description="Minimum normalized intensity")
    max: float = Field(default=1.0, description="Maximum normalized intensity")
    mean: float = Field(..., description="Mean normalized intensity across the image")
    std: float = Field(..., description="Standard deviation of intensity values")
    q90: float = Field(..., description="90th percentile intensity cutoff")
    fraction_at_or_above_0_5: float = Field(..., description="Fraction of pixels with intensity >= 0.5")


class XAIMethodResult(BaseModel):
    """Result payload for a single XAI attribution method."""

    status: str = Field(default="ok", description="Execution status ('ok' or 'failed')")
    heatmap_path: Optional[str] = Field(default=None, description="Local filesystem path to grayscale heatmap PNG")
    heatmap_url: Optional[str] = Field(default=None, description="API URL to retrieve the grayscale heatmap")
    overlay_path: Optional[str] = Field(default=None, description="Local filesystem path to RGB overlay PNG")
    overlay_url: Optional[str] = Field(default=None, description="API URL to retrieve the RGB overlay image")
    normalization: str = Field(
        default="Per-image min-max to [0,1] after method ReLU; constant maps are zero.",
        description="Normalization contract applied to raw attribution tensor",
    )
    statistics: Optional[XAIMethodStats] = Field(default=None, description="Attribution map summary statistics")
    error: Optional[str] = Field(default=None, description="Error code or description if method failed")


class PairwiseSimilarity(BaseModel):
    """Correlation and similarity metrics between two attribution heatmaps."""

    pearson_correlation: Optional[float] = Field(default=None, description="Pearson correlation coefficient r")
    cosine_similarity: Optional[float] = Field(default=None, description="Cosine similarity score")


class XAISummary(BaseModel):
    """Aggregated container for all four XAI methods and cross-method agreement."""

    target: str = Field(default="continuous OSCC sigmoid score", description="Target output of gradient derivation")
    prediction_equivalence_verified: bool = Field(
        default=True,
        description="Verification that intermediate probe output matches full model forward pass",
    )
    methods: Dict[str, XAIMethodResult] = Field(
        ...,
        description="Dictionary of attribution results keyed by method name",
    )
    pairwise_similarity: Dict[str, PairwiseSimilarity] = Field(
        default_factory=dict,
        description="Cross-method agreement metrics for all pairs",
    )
    scope_note: str = Field(
        default="Attribution only; not lesion detection, pathology confirmation, or evidence of cancer.",
        description="Research scope and interpretive limitation note",
    )
