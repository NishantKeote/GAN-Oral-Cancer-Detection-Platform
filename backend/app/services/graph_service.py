"""Neo4j Knowledge Graph Service Module.

Extracted from:
notebooks/OSCC_Integrated_GraphRAG_EfficientNet_XAI_FINAL_FIXED.ipynb (Cells 5, 7)

Responsibilities:
- Thread-safe Neo4j driver connection and session lifecycle management.
- Parameterized Cypher traversal for oral cancer disease relationships and entities.
- Persistence of analyzed case records (Case and Prediction nodes) with relationship edges.
- Graceful offline degradation: returns empty graph context if Neo4j is offline or unconfigured,
  allowing upstream inference and report generation to continue unhindered.
- Strict security: never exposes credentials or passwords in logs, exceptions, or API payloads.
"""

from datetime import datetime, timezone
import json
import re
import threading
import ssl
import certifi
from typing import Any, Dict, List, Optional
from app.config import settings
from app.core.logging import logger

STOPWORDS = {
    "oral", "model", "score", "research", "evidence", "attribution",
    "histopathology", "threshold", "predicted", "normal", "classification",
}

# Parameterized Cypher query for retrieving disease context (Cell 7 verbatim)
DISEASE_CONTEXT_CYPHER = """
MATCH (d:Disease {name:"Oral Squamous Cell Carcinoma"})
OPTIONAL MATCH (d)-[r]-(x)
WITH d,r,x,toLower(coalesce(x.name,"")+" "+coalesce(x.title,"")+" "+coalesce(type(r),"")) AS search_text
WITH d,r,x,reduce(score=0,term IN $terms | score+CASE WHEN term<>"" AND search_text CONTAINS term THEN 1 ELSE 0 END) AS query_overlap
RETURN d.name AS disease,type(r) AS relationship,labels(x) AS node_labels,
       x.name AS node_name,x.title AS node_title,x.paper_id AS paper_id,
       x.year AS year,query_overlap
ORDER BY query_overlap DESC,relationship,node_name,node_title LIMIT 50
"""

# Parameterized Cypher query for case and prediction persistence (Cell 7 verbatim)
CASE_PERSISTENCE_CYPHER = """
MERGE (c:Case {case_id:$case_id})
SET c.filename=$filename,c.age=$age,c.sex=$sex,c.tobacco=$tobacco,c.alcohol=$alcohol,
    c.lesion_site=$lesion_site,c.magnification=$magnification,c.prediction=$prediction,
    c.confidence=$confidence,c.oscc_probability=$oscc_probability,
    c.classification_threshold=$threshold,c.xai_summary_json=$xai_json,
    c.user_question=$user_question,c.updated_at=$updated_at
MERGE (p:Prediction {case_id:$case_id})
SET p.label=$prediction,p.confidence=$confidence,p.oscc_probability=$oscc_probability,
    p.classification_threshold=$threshold,p.xai_summary_json=$xai_json,p.updated_at=$updated_at
MERGE (c)-[:HAS_MODEL_PREDICTION]->(p)
WITH p OPTIONAL MATCH (d:Disease {name:"Oral Squamous Cell Carcinoma"})
FOREACH (_ IN CASE WHEN $prediction="OSCC" AND d IS NOT NULL THEN [1] ELSE [] END |
    MERGE (p)-[:PREDICTS_CLASS]->(d))
"""


class GraphService:
    """Manages Neo4j driver connection, graph queries, and case persistence."""

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ) -> None:
        """Initialize the GraphService with database connection settings."""
        self.uri: str = uri or settings.NEO4J_URI
        self.username: str = username or settings.NEO4J_USERNAME
        self.password: str = password or settings.NEO4J_PASSWORD
        self.database: str = database or settings.NEO4J_DATABASE

        self._driver: Any = None
        self._is_connected: bool = False
        self._lock: threading.Lock = threading.Lock()

    @property
    def is_connected(self) -> bool:
        """Return True if an active verified Neo4j connection is established."""
        return self._is_connected

    def connect(self) -> bool:
        """Establish and verify connection to the Neo4j graph database.

        Preserves exact driver instantiation and verification from Notebook Cell 5:
        - GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        - session.run("RETURN 1 AS ok").single()

        Returns:
            True if connection verified, False otherwise.
        """
        with self._lock:
            if self._is_connected and self._driver is not None:
                return True

            if not self.uri or "your-instance-id" in self.uri:
                logger.info("Neo4j URI is not configured; graph service running in offline degradation mode.")
                self._is_connected = False
                return False

            try:
                from neo4j import GraphDatabase
            except ImportError as exc:
                logger.warning("neo4j driver is not installed in the active environment. Detail: %s", exc)
                self._is_connected = False
                return False

            # Mask URI in logs to prevent accidental credential leakage
            masked_uri = re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", self.uri)
            logger.info("Connecting to Neo4j database instance: %s (database='%s')", masked_uri, self.database)

            try:
                ssl_context = ssl.create_default_context(
                    cafile=certifi.where()
                )

                driver = GraphDatabase.driver(
                    self.uri.replace("neo4j+s://", "neo4j://", 1),
                    auth=(self.username, self.password),
                    encrypted=True,
                    ssl_context=ssl_context,
                )
                with driver.session(database=self.database) as session:
                    session.run("RETURN 1 AS ok").single()

                self._driver = driver
                self._is_connected = True
                logger.info("Neo4j database connection successfully verified.")
                return True

            except Exception as exc:
                logger.warning("Failed to connect to Neo4j instance (%s): %s. Operating in offline fallback mode.", masked_uri, exc)
                self._driver = None
                self._is_connected = False
                return False

    def close(self) -> None:
        """Close Neo4j driver connection cleanly on application shutdown."""
        with self._lock:
            if self._driver is not None:
                try:
                    self._driver.close()
                    logger.info("Neo4j driver connection closed.")
                except Exception as exc:
                    logger.warning("Error closing Neo4j driver: %s", exc)
                finally:
                    self._driver = None
                    self._is_connected = False

    def extract_search_terms(self, retrieval_query: str, max_terms: int = 30) -> List[str]:
        """Extract alphanumeric search keywords (len >= 4) excluding stopwords.

        Preserves exact term extraction from Notebook Cell 7.
        """
        terms: List[str] = []
        for term in re.findall(r"[a-zA-Z]{4,}", retrieval_query.lower()):
            if term not in STOPWORDS and term not in terms:
                terms.append(term)
        return terms[:max_terms]

    def get_disease_context(self, retrieval_query: str) -> List[Dict[str, Any]]:
        """Query Neo4j for connected entities and relationships matching query terms.

        Preserves exact Cypher traversal and term overlap ranking from Notebook Cell 7.
        Provides graceful degradation: returns empty list if Neo4j is offline.

        Args:
            retrieval_query: Semantic query text containing clinical and XAI terms.

        Returns:
            List of dictionaries matching GraphNodeContext schema.
        """
        if not self._is_connected:
            connected = self.connect()
            if not connected or self._driver is None:
                logger.debug("Graph context retrieval skipped: Neo4j is offline or unconfigured.")
                return []

        terms = self.extract_search_terms(retrieval_query, max_terms=30)

        try:
            with self._driver.session(database=self.database) as session:
                result = session.run(DISEASE_CONTEXT_CYPHER, terms=terms)
                records = [dict(r) for r in result]
                logger.info("Retrieved %d graph context records from Neo4j (terms=%d).", len(records), len(terms))
                return records

        except Exception as exc:
            logger.warning("Neo4j disease context query failed: %s. Returning empty graph context.", exc)
            return []

    def save_case(
        self,
        case_id: str,
        filename: str,
        patient_context: Dict[str, str],
        prediction_label: str,
        probability: float,
        xai_summary: Dict[str, Any],
        user_question: str,
    ) -> bool:
        """Persist Case and Prediction nodes with relationships to Neo4j.

        Preserves exact parameterized MERGE operations from Notebook Cell 7:
        - MERGE (c:Case {case_id: $case_id})
        - MERGE (p:Prediction {case_id: $case_id})
        - MERGE (c)-[:HAS_MODEL_PREDICTION]->(p)
        - If prediction == 'OSCC': MERGE (p)-[:PREDICTS_CLASS]->(d:Disease)

        Args:
            case_id: Standardized case identifier string.
            filename: Original uploaded image filename.
            patient_context: Normalized clinical dictionary (age, sex, tobacco, etc.).
            prediction_label: 'OSCC' or 'Normal'.
            probability: Continuous sigmoid score in [0.0, 1.0].
            xai_summary: Full XAI attribution dictionary.
            user_question: User research question.

        Returns:
            True if write consumed successfully, False otherwise.
        """
        if not self._is_connected:
            connected = self.connect()
            if not connected or self._driver is None:
                logger.debug("Graph case persistence skipped: Neo4j is offline or unconfigured.")
                return False

        confidence = probability if prediction_label == "OSCC" else 1.0 - probability
        threshold = settings.CLASSIFICATION_THRESHOLD

        params = {
            "case_id": case_id,
            "filename": filename,
            "age": patient_context.get("age", "Not provided"),
            "sex": patient_context.get("sex", "Not provided"),
            "tobacco": patient_context.get("tobacco", "Not provided"),
            "alcohol": patient_context.get("alcohol", "Not provided"),
            "lesion_site": patient_context.get("lesion_site", "Not provided"),
            "magnification": patient_context.get("magnification", "Not provided"),
            "prediction": prediction_label,
            "confidence": float(confidence),
            "oscc_probability": float(probability),
            "threshold": float(threshold),
            "xai_json": json.dumps(xai_summary, ensure_ascii=False),
            "user_question": user_question or "",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            with self._driver.session(database=self.database) as session:
                session.run(CASE_PERSISTENCE_CYPHER, **params).consume()
            logger.info("Case '%s' successfully persisted to Neo4j knowledge graph.", case_id)
            return True

        except Exception as exc:
            logger.warning("Failed to persist case '%s' to Neo4j: %s", case_id, exc)
            return False


# Global singleton instance
graph_service = GraphService()
