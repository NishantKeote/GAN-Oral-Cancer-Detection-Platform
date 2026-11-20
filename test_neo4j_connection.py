
import sys
import ssl
import certifi

sys.path.insert(0, "backend")

from neo4j import GraphDatabase
from app.config import settings

ssl_context = ssl.create_default_context(
    cafile=certifi.where()
)

print("Testing direct Bolt with verified TLS")
print("Database:", settings.NEO4J_DATABASE)
print("Certificate verification:", ssl_context.verify_mode == ssl.CERT_REQUIRED)

driver = GraphDatabase.driver(
    settings.NEO4J_URI.replace("neo4j+s://", "bolt://", 1),
    auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
    encrypted=True,
    ssl_context=ssl_context,
    connection_timeout=20,
)

try:
    driver.verify_connectivity()
    print("DRIVER CONNECTIVITY: PASSED")

    with driver.session(database=settings.NEO4J_DATABASE) as session:
        result = session.run("RETURN 1 AS result").single()
        print("DATABASE QUERY:", result["result"])

except Exception as error:
    print("ERROR TYPE:", type(error).__name__)
    print("ERROR:", str(error))

finally:
    driver.close()
