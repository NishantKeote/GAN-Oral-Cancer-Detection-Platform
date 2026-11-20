# 06. Database & Knowledge Base Documentation

## 1. Architectural Overview: Dual-Knowledge Subsystem

The platform incorporates a hybrid **GraphRAG** (Graph-augmented Retrieval-Augmented Generation) architecture combining unstructured scientific literature retrieval with structured biomedical ontology traversal.

```
                              ┌─────────────────────────────────────────┐
                              │            Incoming Analysis            │
                              └────────────────────┬────────────────────┘
                                                   │
                         ┌─────────────────────────┴─────────────────────────┐
                         ▼                                                   ▼
         ┌───────────────────────────────┐                   ┌───────────────────────────────┐
         │     Unstructured RAG (FAISS)   │                   │    Structured Graph (Neo4j)   │
         ├───────────────────────────────┤                   ├───────────────────────────────┤
         │ • all-MiniLM-L6-v2 Bi-Encoder │                   │ • Biomedical Ontology Graph   │
         │ • 384-dimensional dense vectors│                   │ • Disease, Risk, Staging Nodes│
         │ • 189 peer-reviewed OSCC chunks│                  │ • Patient Audit Persistence   │
         └───────────────┬───────────────┘                   └───────────────┬───────────────┘
                         │                                                   │
                         └─────────────────────────┬─────────────────────────┘
                                                   ▼
                                 ┌───────────────────────────────────┐
                                 │     Unified Medical Context       │
                                 │      Forwarded to Groq LLM        │
                                 └───────────────────────────────────┘
```

---

## 2. FAISS Dense Vector Database

### 2.1 Storage Specifications

| Property | Value | Notes |
| :--- | :--- | :--- |
| **Index File Path** | `knowledge_base/oscc_literature.faiss` | Binary serialization |
| **File Size** | 290,527 bytes (~290 KB) | Verified on disk |
| **Index Type** | `faiss.IndexFlatIP` | Inner Product on normalized vectors |
| **Vector Dimension** | 384 | Corresponds to `all-MiniLM-L6-v2` |
| **Total Vectors Indexed** | 189 vectors | Chunks extracted from OSCC literature |
| **Metric Equivalence** | Cosine Similarity | Since query and index vectors are $L_2$ unit normalized |

### 2.2 Literature Metadata Store (`knowledge_base/chunk_metadata.json`)
The metadata file contains 189 serialized JSON objects linked 1-to-1 by array index to the FAISS vectors.

```json
{
  "chunk_id": "chunk_0042",
  "paper_id": "PMC_7482910",
  "year": 2021,
  "title": "Histopathological grading and deep learning classification of Oral Squamous Cell Carcinoma",
  "authors": "Patel, R., Sharma, A., Kumar, S.",
  "source_url": "https://doi.org/10.1016/j.oraloncology.2021.105230",
  "chunk_index": 3,
  "text": "Keratin pearl formation and individual cell keratinization are defining hallmarks of well-differentiated oral squamous cell carcinoma. Dyskeratosis and mitotic figures further delineate invasion depth into the subepithelial connective tissue."
}
```

### 2.3 Retrieval Execution Pipeline (`backend/app/services/rag_service.py`)
1. **Query Construction:** Formulates semantic retrieval query based on predicted class and clinical metadata.
2. **Dense Encoding:** Converts query text to 384-dimensional vector via `SentenceTransformer.encode()`.
3. **Normalization:** Normalizes query vector using $L_2$ norm: $\mathbf{q} = \frac{\mathbf{q}}{\|\mathbf{q}\|_2}$.
4. **FAISS Execution:** Performs nearest-neighbor search: `distances, indices = index.search(query_vec, top_k=3)`.
5. **Score Transformation:**
   $$\text{Similarity Score} = \text{clamp}\left(\frac{d + 1.0}{2.0}, 0.0, 1.0\right)$$
6. **Hydration:** Maps indices to metadata objects to produce the final `literature_evidence` payload.

---

## 3. Neo4j Knowledge Graph & Ontology

### 3.1 Connection & Driver Architecture
- **Host Provider:** Neo4j AuraDB (Cloud Managed) or self-hosted Neo4j instance.
- **Protocol:** `bolt+s://` or `neo4j+s://` (TLS encrypted).
- **Service Class:** `backend/app/services/graph_service.py` (`GraphService`).
- **Connection Lifecycle:** Driver created on initial request or application startup, held as a singleton, and closed cleanly during application shutdown.

### 3.2 Graph Schema & Ontological Entities

```
           (:RiskFactor) <──────[:HAS_RISK_FACTOR]──────┐
                                                        │
           (:DiagnosticCriteria) <──[:CHARACTERIZED_BY]──┼── (:Disease {name: 'Oral Squamous Cell Carcinoma'})
                                                        │
           (:StagingCriteria) <─────[:STAGED_BY]────────┘
                                                        ▲
                                                        │ [:EVALUATED_AGAINST]
                                                        │
  (:Patient {id}) ───[:HAS_CASE]───► (:Case {id}) ───[:PRODUCED]───► (:Prediction {score, label})
```

#### Node Labels & Properties
1. **`:Disease`**: Core disease entity.
   - Properties: `name`, `icd10_code`, `description`, `anatomical_sites`.
2. **`:DiagnosticCriteria`**: Pathological indicators.
   - Properties: `name`, `description`, `diagnostic_importance` (`"high"`, `"pathognomonic"`).
3. **`:RiskFactor`**: Epidemiological and behavioral predisposing factors.
   - Properties: `factor`, `category` (`"tobacco"`, `"areca_nut"`, `"alcohol"`, `"hpv"`).
4. **`:Case`**: Patient clinical encounter.
   - Properties: `case_id`, `patient_id`, `created_at`.
5. **`:Prediction`**: Vision pipeline diagnostic output.
   - Properties: `predicted_class`, `probability`, `confidence`, `threshold`.

### 3.3 Cypher Query Specifications

#### Query 1: Contextual Disease Traversal
Executes when an image is classified as OSCC to gather ontological backing for the clinical report:

```cypher
MATCH (d:Disease {name: $disease_name})
OPTIONAL MATCH (d)-[:HAS_RISK_FACTOR]->(r:RiskFactor)
OPTIONAL MATCH (d)-[:CHARACTERIZED_BY]->(c:DiagnosticCriteria)
OPTIONAL MATCH (d)-[:STAGED_BY]->(s:StagingCriteria)
RETURN 
    d.name AS disease,
    d.description AS overview,
    collect(DISTINCT r.factor) AS risk_factors,
    collect(DISTINCT c.name) AS diagnostic_features,
    collect(DISTINCT s.criteria) AS staging_rules
```

#### Query 2: Clinical Case Audit Trail Persistence
Persists diagnosis, timestamp, and generated artifacts to maintain non-repudiable medical audit logs:

```cypher
MERGE (p:Patient {patient_id: $patient_id})
CREATE (c:Case {
    case_id: $case_id,
    timestamp: datetime($timestamp),
    notes: $clinical_notes
})
CREATE (pred:Prediction {
    predicted_class: $predicted_class,
    probability: $probability,
    confidence: $confidence,
    threshold: $threshold,
    gradcam_path: $gradcam_url,
    hirescam_path: $hirescam_url
})
MERGE (p)-[:HAS_CASE]->(c)
CREATE (c)-[:PRODUCED_PREDICTION]->(pred)
```

---

## 4. Graceful Degradation & Resilience

In clinical production environments, external graph database outages must never prevent emergency diagnostic image evaluation.

```python
# Graceful degradation logic in GraphService
try:
    with self._driver.session() as session:
        result = session.run(query, parameters)
        return self._format_results(result)
except (ServiceUnavailable, AuthError, Exception) as exc:
    logger.warning("Neo4j graph query failed. Operating in degraded mode: %s", exc)
    return {
        "status": "degraded",
        "error": "Graph database unreachable",
        "entities": []
    }
```

- If `NEO4J_URI` is blank or unconfigured, `GraphService.is_available` returns `False` immediately, bypassing network timeouts.
- The pipeline proceeds to LLM report synthesis using only FAISS literature chunks, setting `status="degraded"` in the API response.

---

## 5. Maintenance, Re-indexing & Updates

1. **FAISS Index Rebuilding:** To update scientific literature, run an offline embedding script:
   - Chunk new PDF/text articles into 300–500 character spans with 50-character overlap.
   - Embed using `SentenceTransformer("all-MiniLM-L6-v2")`.
   - Recreate index with `faiss.IndexFlatIP(384)` and serialize to `knowledge_base/oscc_literature.faiss`.
   - Update `knowledge_base/chunk_metadata.json` atomically.
2. **Data Backup:** Both `oscc_literature.faiss` and `chunk_metadata.json` are committed directly to version control or object storage, ensuring 100% reproducible cold starts without external database provisioning.
