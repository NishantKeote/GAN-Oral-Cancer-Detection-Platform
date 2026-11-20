import sys
import ssl
import certifi

sys.path.insert(0, "backend")

from app.config import settings
from neo4j import GraphDatabase

uri = settings.NEO4J_URI.replace("neo4j+s://", "bolt://", 1)
ssl_context = ssl.create_default_context(cafile=certifi.where())

driver = GraphDatabase.driver(
    uri,
    auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
    encrypted=True,
    ssl_context=ssl_context,
    connection_timeout=20,
)

try:
    driver.verify_connectivity()
    print("DIRECT CONNECTION: PASSED")

    with driver.session(database="system") as session:
        for record in session.run("SHOW DATABASES"):
            print(dict(record))

except Exception as error:
    print("ERROR:", type(error).__name__)
    print(str(error))

finally:
    driver.close()
