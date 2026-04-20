from neo4j import GraphDatabase

URI = "bolt://neo4j-service:7687"
USERNAME = "neo4j"
PASSWORD = "Ria05@10"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))