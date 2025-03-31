import rdflib
from py2neo import Graph as NeoGraph, Node, Relationship
from rdflib.namespace import RDF, RDFS, OWL

username = "neo4j"
password = "12345"
file = "example.owl"
format = "xml"

# Connect to Neo4j
def connectNeo4j(username, password):
   neo4j_graph = NeoGraph("bolt://localhost:7687", auth=(username, password))
   return neo4j_graph

# Load OWL file
def loadOWL(filename, format):
   rdf_graph = rdflib.Graph()
   rdf_graph.parse("example.owl", format="xml")
   return rdf_graph


def mapOWLtoLPG():

   # Create and clear Neo4j database
   neo4j_graph = connectNeo4j(username=username, password=password)
   neo4j_graph.delete_all()
   
   #create graph
   rdf_graph = loadOWL(file, format)

   # Store nodes for individuals and classes
   nodes = {}

   # Step 1: Process OWL Classes and Create LPG Nodes
   for subj, _, obj in rdf_graph.triples((None, RDF.type, OWL.Class)):
      class_name = subj.split("/")[-1]  # Extract class name
      class_node = Node("Class", name=class_name)
      nodes[subj] = class_node
      neo4j_graph.create(class_node)

   # Step 2: Process Individuals and Assign Classes
   for subj, _, obj in rdf_graph.triples((None, RDF.type, None)):
      if obj in nodes:  # If the object is a known class
         class_name = nodes[obj]["name"]
         individual_name = subj.split("/")[-1]
         individual_node = Node(class_name, name=individual_name)
         nodes[subj] = individual_node
         neo4j_graph.create(individual_node)

   # Step 3: Process Object Properties (Relationships)
   for subj, pred, obj in rdf_graph.triples((None, None, None)):
      if pred not in [RDF.type, RDFS.subClassOf]:  # Skip type declarations
         rel_name = pred.split("/")[-1]
         if subj in nodes and obj in nodes:
               relationship = Relationship(nodes[subj], rel_name, nodes[obj])
               neo4j_graph.create(relationship)

   print("OWL to LPG Conversion Complete!")

mapOWLtoLPG()
