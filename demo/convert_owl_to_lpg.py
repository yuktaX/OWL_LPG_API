import rdflib
from rdflib import Graph, URIRef, RDF
from py2neo import Graph as NeoGraph, Node, Relationship

# Load OWL file
rdf_graph = Graph()

#creates an in-memory representation of the ontology.
rdf_graph.parse("example.owl", format="xml")

# Connect to Neo4j
neo4j_graph = NeoGraph("bolt://localhost:7687", auth=("neo4j", "12345")) #auth=("kt", "neo4j_kt")

# Clear previous data
neo4j_graph.delete_all()

# Extract and insert nodes
nodes = {}
for subj, rdf_type, obj in rdf_graph.triples((None, RDF.type, None)):
    label = obj.split("/")[-1]  # Get class name
    node_name = subj.split("/")[-1]  # Get individual name
    node = Node(label, name=node_name)
    nodes[subj] = node
    neo4j_graph.create(node)

print("Nodes are - ", nodes)

# Extract and insert relationships
for subj, pred, obj in rdf_graph.triples((None, None, None)):
    if pred != RDF.type:  # Skip class declarations
        rel_name = pred.split("/")[-1]
        if subj in nodes and obj in nodes:
            relationship = Relationship(nodes[subj], rel_name, nodes[obj])
            neo4j_graph.create(relationship)

print("OWL to LPG Conversion Complete!")

