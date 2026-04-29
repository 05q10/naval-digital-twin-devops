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
        messages = [record["message"] for record in result]

        return {
            "status": "🚀 CI/CD LIVE",
            "data": [record["message"] for record in result],
            "version": "v3"
        }

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

@app.get("/graph/load-json")
def load_json_graph():

    import os
    import json
    from app.db.neo4j import driver

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "..", "data", "final_naval.json")

    if not os.path.exists(file_path):
        return {"error": f"JSON file not found at {file_path}"}

    with open(file_path) as f:
        data = json.load(f)

    created_nodes = 0
    created_edges = 0

    # 🔹 CLEAN PROPERTIES
    def clean_properties(props):
        clean = {}
        for k, v in props.items():
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            elif v is None:
                clean[k] = None
            else:
                clean[k] = json.dumps(v)
        return clean

    # 🔹 TRANSACTION FUNCTION (CRITICAL FIX)
    def create_node(tx, node_type, node_id, props):
        query = f"""
        MERGE (n:{node_type} {{node_id: $node_id}})
        SET n = $props
        """
        tx.run(query, node_id=node_id, props=props)

    def create_relationship(tx, rel_type, from_id, to_id, props):
        query = f"""
        MATCH (a {{node_id: $from_id}})
        MATCH (b {{node_id: $to_id}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r = $props
        """
        tx.run(query, from_id=from_id, to_id=to_id, props=props)

    with driver.session() as session:

        print("===== LOADING NODES =====")

        # =========================
        # 🔹 LOAD NODES
        # =========================
        for node_type, content in data.get("node_types", {}).items():

            nodes = content.get("nodes", [])

            for node in nodes:
                node_id = node.get("node_id")

                if not node_id:
                    continue

                props = node.get("properties", {})
                clean_props = clean_properties(props)
                clean_props["node_id"] = node_id

                print("CREATING NODE:", node_id)

                session.execute_write(
                    create_node,
                    node_type,
                    node_id,
                    clean_props
                )

                created_nodes += 1

        print("===== LOADING RELATIONSHIPS =====")

        # =========================
        # 🔹 LOAD RELATIONSHIPS
        # =========================
        for rel_type, content in data.get("relationship_types", {}).items():

            edges = content.get("edges", [])

            for edge in edges:
                from_id = edge.get("from")
                to_id = edge.get("to")

                if not from_id or not to_id:
                    continue

                props = edge.get("properties", {})
                clean_props = clean_properties(props)

                print(f"CREATING EDGE: {from_id} -> {to_id}")

                session.execute_write(
                    create_relationship,
                    rel_type,
                    from_id,
                    to_id,
                    clean_props
                )

                created_edges += 1

    return {
        "status": "graph fully loaded (no duplicates)",
        "nodes_processed": created_nodes,
        "edges_processed": created_edges
    }