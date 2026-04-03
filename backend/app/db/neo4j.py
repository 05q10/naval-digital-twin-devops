from neo4j import GraphDatabase

URI = "bolt://neo4j:7687"
USERNAME = "neo4j"
PASSWORD = "password"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))