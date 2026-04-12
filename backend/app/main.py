from fastapi import FastAPI
from app.db.neo4j import driver
import json
import os

app = FastAPI()

# ------------------ BASIC ROUTES ------------------

@app.get("/")
def home():
    return {"message": "NDTP running"}

@app.get("/health")
def health():
    return {"status": "ok"}


# ------------------ TEST NEO4J ------------------

@app.get("/graph/test")
def test_graph():
    with driver.session() as session:
        result = session.run("RETURN 'Neo4j Connected' AS message")
        return [record["message"] for record in result]


# ------------------ OLD DEMO GRAPH ------------------

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
    return {"status": "demo graph loaded"}


@app.get("/graph/motor")
def get_motor():
    with driver.session() as session:
        result = session.run("""
        MATCH (m:Motor)-[:HAS_SYSTEM]->(s)-[:HAS_EQUIPMENT]->(e)
        RETURN m.motor_uid AS motor, s.name AS system, e.name AS equipment
        """)
        return [dict(record) for record in result]


# ------------------ NEW: LOAD JSON GRAPH ------------------

@app.post("/graph/load-json")
def load_json_graph():

    import os
    import json

    file_path = os.path.join("data", "final_naval.json")

    if not os.path.exists(file_path):
        return {"error": f"JSON file not found at {file_path}"}

    with open(file_path) as f:
        data = json.load(f)

    created_nodes = 0

    def clean_properties(props):
        clean = {}
        for k, v in props.items():
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            else:
                # 🔥 convert nested dict/list → string
                clean[k] = json.dumps(v)
        return clean

    with driver.session() as session:

        # 🔹 LOAD NODES
        for node_type, content in data.get("node_types", {}).items():

            for node in content.get("nodes", []):
                node_id = node.get("node_id")
                props = node.get("properties", {})

                clean_props = clean_properties(props)
                clean_props["node_id"] = node_id

                query = f"""
                MERGE (n:{node_type} {{node_id: $node_id}})
                SET n += $props
                """

                session.run(query, node_id=node_id, props=clean_props)
                created_nodes += 1

    return {
        "status": "nodes loaded successfully",
        "nodes_processed": created_nodes
    }