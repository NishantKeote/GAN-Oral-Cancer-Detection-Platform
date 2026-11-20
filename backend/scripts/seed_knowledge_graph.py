
import json
import ssl
import sys
from pathlib import Path

import certifi
from neo4j import GraphDatabase

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
METADATA_FILE = PROJECT_ROOT / "knowledge_base" / "chunk_metadata.json"

sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings


DISEASE_NAME = "Oral Squamous Cell Carcinoma"


def load_metadata():
    """Load and validate the literature metadata."""
    with METADATA_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    required = {
        "chunk_id", "paper_id", "year", "title",
        "authors", "source_url", "chunk_index", "text"
    }

    for index, record in enumerate(records):
        missing = required - record.keys()
        if missing:
            raise ValueError(
                f"Record {index} is missing fields: {sorted(missing)}"
            )

    return records


def seed_graph(driver, records):
    """Create disease, paper and chunk nodes idempotently."""

    papers = {}

    for record in records:
        paper_id = record["paper_id"]

        paper = {
            "paper_id": paper_id,
            "title": record["title"],
            "name": record["title"],
            "year": record["year"],
            "authors": record["authors"],
            "source_url": record["source_url"],
        }

        if paper_id in papers and papers[paper_id] != paper:
            raise ValueError(
                f"Inconsistent metadata found for paper: {paper_id}"
            )

        papers[paper_id] = paper

    with driver.session(database=settings.NEO4J_DATABASE) as session:

        # Uniqueness constraints
        session.run("""
            CREATE CONSTRAINT disease_name_unique IF NOT EXISTS
            FOR (d:Disease)
            REQUIRE d.name IS UNIQUE
        """).consume()

        session.run("""
            CREATE CONSTRAINT paper_id_unique IF NOT EXISTS
            FOR (p:Paper)
            REQUIRE p.paper_id IS UNIQUE
        """).consume()

        session.run("""
            CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
            FOR (c:Chunk)
            REQUIRE c.chunk_id IS UNIQUE
        """).consume()

        # Create disease node
        session.run("""
            MERGE (d:Disease {name: $name})
        """, name=DISEASE_NAME).consume()

        # Create research paper nodes and disease relationships
        paper_records = list(papers.values())

        session.run("""
            MATCH (d:Disease {name: $disease_name})
            UNWIND $papers AS item

            MERGE (p:Paper {paper_id: item.paper_id})
            SET p.name = item.name,
                p.title = item.title,
                p.year = item.year,
                p.authors = item.authors,
                p.source_url = item.source_url

            MERGE (d)-[:HAS_RESEARCH_PAPER]->(p)
        """, disease_name=DISEASE_NAME, papers=paper_records).consume()

        # Create literature chunks and connect them to papers
        session.run("""
            UNWIND $chunks AS item

            MATCH (p:Paper {paper_id: item.paper_id})

            MERGE (c:Chunk {chunk_id: item.chunk_id})
            SET c.paper_id = item.paper_id,
                c.chunk_index = item.chunk_index,
                c.year = item.year,
                c.title = item.title,
                c.text = item.text

            MERGE (p)-[:HAS_CHUNK]->(c)
        """, chunks=records).consume()

        # Verify graph counts
        result = session.run("""
            MATCH (d:Disease)
            WHERE d.name = $disease_name
            OPTIONAL MATCH (d)-[:HAS_RESEARCH_PAPER]->(p:Paper)
            OPTIONAL MATCH (p)-[:HAS_CHUNK]->(c:Chunk)
            RETURN count(DISTINCT d) AS diseases,
                   count(DISTINCT p) AS papers,
                   count(DISTINCT c) AS chunks
        """, disease_name=DISEASE_NAME).single()

        return dict(result)


def main():
    if not settings.NEO4J_URI:
        raise RuntimeError("NEO4J_URI is not configured.")

    if not settings.NEO4J_USERNAME or not settings.NEO4J_PASSWORD:
        raise RuntimeError("Neo4j credentials are not configured.")

    records = load_metadata()

    print("Loaded literature chunks:", len(records))
    print("Unique papers:", len({r["paper_id"] for r in records}))

    uri = settings.NEO4J_URI
    if uri.startswith("neo4j+s://"):
        uri = uri.replace("neo4j+s://", "neo4j://", 1)

    ssl_context = ssl.create_default_context(
        cafile=certifi.where()
    )

    driver = GraphDatabase.driver(
        uri,
        auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
        encrypted=True,
        ssl_context=ssl_context,
    )

    try:
        driver.verify_connectivity()
        print("Neo4j connectivity: PASSED")

        counts = seed_graph(driver, records)

        print("\n--- KNOWLEDGE GRAPH INGESTION ---")
        print("Disease nodes:", counts["diseases"])
        print("Paper nodes:", counts["papers"])
        print("Chunk nodes:", counts["chunks"])
        print("Ingestion: COMPLETED")

    finally:
        driver.close()
        print("Neo4j connection closed.")


if __name__ == "__main__":
    main()
