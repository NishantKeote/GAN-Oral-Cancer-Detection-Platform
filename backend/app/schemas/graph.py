"""Knowledge graph context schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class GraphNodeContext(BaseModel):
    """Contextual entity or disease relationship retrieved from Neo4j."""

    disease: str = Field(..., description="Root disease entity name")
    relationship: Optional[str] = Field(default=None, description="Cypher relationship type")
    node_labels: List[str] = Field(default_factory=list, description="Labels assigned to the connected node")
    node_name: Optional[str] = Field(default=None, description="Name property of the connected node")
    node_title: Optional[str] = Field(default=None, description="Title property of the connected node")
    paper_id: Optional[str] = Field(default=None, description="PubMed Central paper ID identifier")
    year: Optional[int] = Field(default=None, description="Publication year")
    query_overlap: int = Field(default=0, description="Count of overlapping search terms")
