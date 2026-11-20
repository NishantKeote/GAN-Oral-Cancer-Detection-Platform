"""Retrieval-Augmented Generation (RAG) literature schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LiteratureEvidenceChunk(BaseModel):
    """Retrieved scientific literature evidence chunk from the FAISS vector database."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    paper_id: str = Field(..., description="PubMed Central paper accession number")
    year: Optional[int] = Field(default=None, description="Publication year")
    title: str = Field(..., description="Article title")
    authors: str = Field(..., description="Author list")
    source_url: str = Field(..., description="PubMed Central canonical URL")
    chunk_index: int = Field(default=0, description="Index of this chunk within the paper")
    text: str = Field(..., description="Extracted textual excerpt")
    similarity: float = Field(..., description="Cosine similarity score from vector retrieval")
    graph_entity_matches: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Correlated Neo4j graph entities sharing the same paper_id",
    )
