"""Retrieval-Augmented Generation (RAG) and Knowledge Base Service Module.

Extracted from:
notebooks/OSCC_Integrated_GraphRAG_EfficientNet_XAI_FINAL_FIXED.ipynb (Cells 4, 7)

Responsibilities:
- Thread-safe singleton loading of the FAISS index (oscc_literature.faiss) and metadata (chunk_metadata.json).
- SentenceTransformer embedding model initialization ('sentence-transformers/all-MiniLM-L6-v2', 384 dimensions).
- Dynamic query construction assembling model predictions, continuous scores, patient metadata, and XAI statistics.
- Vector similarity search (top-k inner product on normalized embeddings, equivalent to cosine similarity).
- Mapping returned vector indices to chunk metadata records.
- Correlating retrieved literature chunks to matching Neo4j graph entities by paper_id.
- Safe error handling, boundary validation, and graceful failure recovery.
"""

import json
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional
import numpy as np
from app.config import settings
from app.core.logging import logger

EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION: int = 384
DEFAULT_TOP_K: int = 5


class RAGService:
    """Manages semantic embeddings, FAISS vector search, query assembly, and literature evidence."""

    def __init__(
        self,
        faiss_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
        model_name: str = EMBEDDING_MODEL_NAME,
    ) -> None:
        """Initialize the RAGService with resource paths and embedding model name."""
        self.faiss_path: Path = faiss_path or settings.FAISS_PATH
        self.metadata_path: Path = metadata_path or settings.METADATA_PATH
        self.model_name: str = model_name

        self._faiss_index: Any = None
        self._chunk_metadata: List[Dict[str, Any]] = []
        self._embedder: Any = None
        self._is_loaded: bool = False
        self._lock: threading.Lock = threading.Lock()

    @property
    def is_loaded(self) -> bool:
        """Return True if FAISS index, metadata, and embedder are loaded."""
        return self._is_loaded

    @property
    def faiss_index(self) -> Any:
        """Access underlying FAISS index, loading resources if necessary."""
        self.ensure_resources_loaded()
        return self._faiss_index

    @property
    def chunk_metadata(self) -> List[Dict[str, Any]]:
        """Access chunk metadata list, loading resources if necessary."""
        self.ensure_resources_loaded()
        return self._chunk_metadata

    @property
    def embedder(self) -> Any:
        """Access SentenceTransformer embedder, loading resources if necessary."""
        self.ensure_resources_loaded()
        return self._embedder

    def load_resources(self) -> None:
        """Load the pre-indexed FAISS index, chunk metadata JSON, and embedder model.

        Preserves exact loading contracts from Notebook Cell 4:
        - faiss_index = faiss.read_index(FAISS_PATH)
        - chunk_metadata = json.load(f)
        - embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        """
        with self._lock:
            if self._is_loaded:
                return

            # 1. Validate file existence
            if not self.faiss_path.is_file():
                err_msg = f"FAISS index file not found at: {self.faiss_path}"
                logger.error(err_msg)
                raise FileNotFoundError(err_msg)

            if not self.metadata_path.is_file():
                err_msg = f"Chunk metadata JSON file not found at: {self.metadata_path}"
                logger.error(err_msg)
                raise FileNotFoundError(err_msg)

            # 2. Import vector search and NLP libraries
            try:
                import faiss
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                err_msg = "faiss or sentence-transformers is not installed in the active environment."
                logger.error("%s Detail: %s", err_msg, exc)
                raise RuntimeError(err_msg) from exc

            # 3. Load metadata records
            logger.info("Loading literature chunk metadata from: %s", self.metadata_path)
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                if not isinstance(metadata, list):
                    raise ValueError(f"Chunk metadata must be a list of records; got {type(metadata)}")
                self._chunk_metadata = metadata
            except Exception as exc:
                logger.exception("Failed to parse chunk metadata JSON from %s", self.metadata_path)
                raise RuntimeError(f"Metadata loading error: {exc}") from exc

            # 4. Load FAISS index
            logger.info("Loading FAISS index from: %s", self.faiss_path)
            try:
                index = faiss.read_index(str(self.faiss_path))
                if index.d != EMBEDDING_DIMENSION:
                    raise ValueError(
                        f"FAISS index dimension mismatch: found {index.d}, expected {EMBEDDING_DIMENSION}"
                    )
                if index.ntotal != len(self._chunk_metadata):
                    logger.warning(
                        "FAISS vector count (%d) differs from metadata record count (%d)",
                        index.ntotal,
                        len(self._chunk_metadata),
                    )
                self._faiss_index = index
            except Exception as exc:
                logger.exception("Failed to read FAISS index from %s", self.faiss_path)
                raise RuntimeError(f"FAISS loading error: {exc}") from exc

            # 5. Load SentenceTransformer embedder
            logger.info("Initializing SentenceTransformer model: %s", self.model_name)
            try:
                self._embedder = SentenceTransformer(self.model_name)
            except Exception as exc:
                logger.exception("Failed to initialize SentenceTransformer model '%s'", self.model_name)
                raise RuntimeError(f"SentenceTransformer initialization error: {exc}") from exc

            self._is_loaded = True
            logger.info(
                "RAG resources successfully loaded: %d FAISS vectors (dim=%d), %d metadata records.",
                self._faiss_index.ntotal,
                self._faiss_index.d,
                len(self._chunk_metadata),
            )

    def ensure_resources_loaded(self) -> None:
        """Thread-safe helper ensuring FAISS index and embedder are initialized."""
        if not self._is_loaded:
            self.load_resources()

    def xai_retrieval_terms(self, xai_summary: Dict[str, Any]) -> str:
        """Format attribution statistics and cross-method agreement text for retrieval.

        Preserves exact logic from Notebook Cell 7:
        - Summarizes mean intensity and q90 per active method.
        - Computes mean Pearson similarity across all available pairs.
        """
        summaries: List[str] = []
        for name, item in xai_summary.get("methods", {}).items():
            if isinstance(item, dict) and item.get("status") == "ok":
                stats = item.get("statistics", {})
                mean_val = stats.get("mean", 0.0)
                q90_val = stats.get("q90", 0.0)
                summaries.append(f"{name} attribution summary mean {mean_val:.3f} q90 {q90_val:.3f}")

        agreement = xai_summary.get("pairwise_similarity", {})
        correlations: List[float] = [
            v.get("pearson_correlation")
            for v in agreement.values()
            if isinstance(v, dict) and v.get("pearson_correlation") is not None
        ]

        if correlations:
            mean_corr = round(float(np.mean(correlations)), 3)
            agreement_text = f"attribution map agreement mean Pearson similarity {mean_corr}"
        else:
            agreement_text = "attribution map agreement unavailable"

        summaries.append(agreement_text)
        return "; ".join(summaries) if summaries else "No usable attribution maps were generated."

    def build_case_query(
        self,
        prediction_label: str,
        oscc_probability: float,
        patient_context: Dict[str, str],
        user_question: str,
        xai_summary: Dict[str, Any],
    ) -> str:
        """Assemble the dynamic semantic retrieval query string.

        Preserves exact formulation from Notebook Cell 7:
        - Root histopathology research premise
        - Predicted diagnostic class and sigmoid score
        - Optimal classification threshold
        - XAI statistical terms and cross-method agreement
        - Normalized patient metadata (age, sex, tobacco, alcohol, site, magnification)
        - Optional user research question
        - Disclaimer suffix
        """
        threshold = settings.CLASSIFICATION_THRESHOLD
        parts: List[str] = [
            "oral squamous cell carcinoma histopathology research evidence",
            f"classifier predicted class {prediction_label}",
            f"OSCC sigmoid score {oscc_probability:.6f}",
            f"fixed classification threshold {threshold:.6f}",
            self.xai_retrieval_terms(xai_summary),
        ]

        for key, value in patient_context.items():
            if value and value != "Not provided":
                parts.append(f"{key}: {value}")

        clean_question = user_question.strip() if user_question else ""
        if clean_question:
            parts.append(f"research question: {clean_question}")

        parts.append("model attribution is not a pathological finding")
        return " ".join(parts)

    def retrieve_literature(self, query: str, top_k: int = DEFAULT_TOP_K) -> List[Dict[str, Any]]:
        """Encode query text and perform FAISS top-k vector similarity search.

        Preserves exact retrieval contract from Notebook Cell 7:
        1. embedder.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype('float32')
        2. scores, indices = faiss_index.search(embedding, top_k)
        3. Bounds check: 0 <= idx < len(chunk_metadata)
        4. item = dict(chunk_metadata[idx]); item['similarity'] = float(score)

        Args:
            query: Semantic retrieval query text.
            top_k: Number of nearest neighbor literature chunks to return.

        Returns:
            List of literature evidence dictionaries matching LiteratureEvidenceChunk schema.
        """
        if not query or not query.strip():
            query = "oral squamous cell carcinoma histopathology research evidence"

        self.ensure_resources_loaded()

        try:
            # Generate normalized float32 query embedding vector of shape (1, 384)
            embedding = self._embedder.encode(
                [query],
                normalize_embeddings=True,
                convert_to_numpy=True,
            ).astype("float32")

            scores, indices = self._faiss_index.search(embedding, top_k)
            results: List[Dict[str, Any]] = []

            for score, idx in zip(scores[0], indices[0]):
                int_idx = int(idx)
                if int_idx < 0 or int_idx >= len(self._chunk_metadata):
                    continue

                item = dict(self._chunk_metadata[int_idx])
                item["similarity"] = float(score)
                item["graph_entity_matches"] = []
                results.append(item)

            logger.info("Retrieved %d literature chunks for query (top_k=%d).", len(results), top_k)
            return results

        except Exception as exc:
            logger.exception("FAISS vector retrieval failed for query: %s", query[:80])
            raise RuntimeError(f"Vector search execution error: {exc}") from exc

    def connect_literature_to_graph(
        self,
        literature_evidence: List[Dict[str, Any]],
        graph_context: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Correlate retrieved literature chunks with matching Neo4j graph nodes.

        Preserves exact entity linking logic from Notebook Cell 7:
        - Groups graph entities by matching paper_id string.
        - Populates 'graph_entity_matches' on each literature chunk.

        Args:
            literature_evidence: List of retrieved literature chunk dictionaries.
            graph_context: List of graph nodes retrieved from Neo4j.

        Returns:
            Updated literature evidence list with linked graph entities.
        """
        by_paper: Dict[str, List[Dict[str, Any]]] = {}
        for node in graph_context:
            paper_id = node.get("paper_id")
            if paper_id is not None:
                entity = {
                    k: node.get(k)
                    for k in ("node_labels", "node_name", "node_title", "relationship")
                }
                by_paper.setdefault(str(paper_id), []).append(entity)

        linked: List[Dict[str, Any]] = []
        for item in literature_evidence:
            evidence = dict(item)
            paper_id = evidence.get("paper_id")
            evidence["graph_entity_matches"] = (
                by_paper.get(str(paper_id), []) if paper_id is not None else []
            )
            linked.append(evidence)

        return linked


# Global singleton instance
rag_service = RAGService()
