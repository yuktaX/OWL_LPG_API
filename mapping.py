import rdflib
from py2neo import Graph as NeoGraph, Node, Relationship
from rdflib.namespace import RDF, RDFS, OWL

username = "neo4j"  #put your own neo4j username here
password = "12345"  #put your own password here
format = "xml"

class Mapper:
   def __init__(self, username, password, format="xml"):
      self.username = username
      self.password = password
      self.format = format
      self.neo4j_graph = None

   def connect_neo4j(self):
      self.neo4j_graph = NeoGraph("bolt://localhost:7687", auth=(self.username, self.password))
      return self.neo4j_graph

   def load_owl(self, filename):
      rdf_graph = rdflib.Graph()
      rdf_graph.parse(filename, format=self.format)
      return rdf_graph

   def map_owl_to_lpg(self, filename):
      # Connect to Neo4j and clear the database
      self.connect_neo4j()
      self.neo4j_graph.delete_all()

      # Load OWL file
      rdf_graph = self.load_owl(filename)

      # Store nodes for individuals and classes
      nodes = {}

      # Step 1: Process OWL Classes and Create LPG Nodes
      for subj, _, obj in rdf_graph.triples((None, RDF.type, OWL.Class)):
         class_name = subj.split("/")[-1]  # Extract class name
         class_node = Node("Class", name=class_name)
         nodes[subj] = class_node
         self.neo4j_graph.create(class_node)

      # Step 2: Process Individuals and Assign Classes
      for subj, _, obj in rdf_graph.triples((None, RDF.type, None)):
         if obj in nodes:  # If the object is a known class
            class_name = nodes[obj]["name"]
            individual_name = subj.split("/")[-1]
            individual_node = Node(class_name, name=individual_name)
            nodes[subj] = individual_node
            self.neo4j_graph.create(individual_node)

      # Step 3: Process Object Properties (Relationships)
      for subj, pred, obj in rdf_graph.triples((None, None, None)):
         if pred not in [RDF.type, RDFS.subClassOf]:  # Skip type declarations
            rel_name = pred.split("/")[-1]
            if subj in nodes and obj in nodes:
               relationship = Relationship(nodes[subj], rel_name, nodes[obj])
               self.neo4j_graph.create(relationship)

      print("OWL to LPG Conversion Complete!")

test = Mapper(username, password, format)
test.map_owl_to_lpg("PizzaOntologyOWL.owl")
