import sys
import ssl
import certifi

sys.path.insert(0, "backend")

from app.config import settings
from neo4j import GraphDatabase

uri = settings.NEO4J_URI.replace("neo4j+s://", "neo4j://", 1)

ssl_context = ssl.create_default_context(
    cafile=certifi.where()
)

driver = GraphDatabase.driver(
    uri,
    auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
    encrypted=True,
    ssl_context=ssl_context,
    connection_timeout=20,
)

try:
    print("Testing Neo4j routing with verified TLS...")
    driver.verify_connectivity()
    print("ROUTING CONNECTIVITY: PASSED")

    with driver.session(database=settings.NEO4J_DATABASE) as session:
        result = session.run("RETURN 1 AS result").single()
        print("DATABASE QUERY:", result["result"])

except Exception as error:
    print("ERROR TYPE:", type(error).__name__)
    print("ERROR:", str(error))

finally:
    driver.close()
