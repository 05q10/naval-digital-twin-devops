from fastapi import FastAPI
from app.db.neo4j import driver
app = FastAPI()

@app.get("/")
def home():
    return {"message": "NDTP running"}

@app.get("/graph/test")
def test_graph():
    with driver.session() as session:
        result = session.run("RETURN 'Neo4j Connected' AS message")
        return [record["message"] for record in result]
    
@app.get("/graph/load")
def load_graph():
    with driver.session() as session:
        session.run("""
        CREATE (m:Motor {motor_uid: 'MOTOR_001'})
        CREATE (s:System {name: 'Fuel System'})
        CREATE (e:Equipment {name: 'Pump'})
        CREATE (m)-[:HAS_SYSTEM]->(s)
        CREATE (s)-[:HAS_EQUIPMENT]->(e)
        """)
    return {"status": "graph loaded"}

@app.get("/graph/motor")
def get_motor():
    with driver.session() as session:
        result = session.run("""
        MATCH (m:Motor)-[:HAS_SYSTEM]->(s)-[:HAS_EQUIPMENT]->(e)
        RETURN m.motor_uid AS motor, s.name AS system, e.name AS equipment
        """)
        return [dict(record) for record in result]

@app.get("/health")
def health():
    return {"status": "ok"}