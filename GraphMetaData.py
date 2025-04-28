from py2neo import *
from owlready2 import owl
from OWLHelper import OWLHelper
from Connector import Connector
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GraphMetaData:
   def __init__(self, filename, neo4j_graph):
      self.owl_helper = OWLHelper(filename, format)
      self.onto = self.owl_helper.load_owl_ontology()
      self.neo4j_graph = neo4j_graph
      self.edge_names = {"inverse":"INVERSE_OF", "transitive": "TRANSITIVE", "subprop":"SUBPROPERTY_OF", "disjoint":"DISJOINT"}
   
   def add_inverse_properties(self):
      for prop in self.onto.object_properties():
         if prop.inverse_property:
            inverse_prop = prop.inverse_property
            
            # Create nodes for each OP, the original property is the inverse of its inverse
            inverse_node_1 = Node("ObjectProperty", name=self.owl_helper.extract_local_name(prop.iri))
            inverse_node_2 = Node("ObjectProperty", name=self.owl_helper.extract_local_name(inverse_prop.iri))
            
            # Create a relationship indicating they are inverses
            inverse_relationship = Relationship(inverse_node_1, self.edge_names["inverse"], inverse_node_2)
            
            # Add the nodes and relationship to the graph
            self.neo4j_graph.merge(inverse_node_1, "ObjectProperty", "name")
            self.neo4j_graph.merge(inverse_node_2, "ObjectProperty", "name")
            self.neo4j_graph.merge(inverse_relationship)
            
   def add_transitive_properties(self):
      for prop in self.onto.object_properties():
         if owl.TransitiveProperty in prop.is_a:
            # Create a node for the transitive property
            transitive_node = Node("ObjectProperty", name=self.owl_helper.extract_local_name(prop.iri))
            
            # Create a self-relationship indicating it is transitive
            transitive_relationship = Relationship(transitive_node, self.edge_names["transitive"], transitive_node)
            
            # Add the node and relationship to the graph
            self.neo4j_graph.merge(transitive_node, "ObjectProperty", "name")
            self.neo4j_graph.merge(transitive_relationship)
   
   def add_object_subproperties(self):
      for prop in self.onto.object_properties():
         for superprop in prop.is_a:
            
            # Skip if the property is a TransitiveProperty or ObjectProperty owl base property itself
            if self.owl_helper.extract_local_name(superprop.iri) in ["TransitiveProperty", "ObjectProperty"]:
                  continue
            
            parent_node = Node("ObjectProperty", name=self.owl_helper.extract_local_name(superprop.iri))
            node = Node("ObjectProperty", name=self.owl_helper.extract_local_name(prop.iri))
            
            # Create a relationship indicating the subproperty            
            subproperty_relationship = Relationship(node, self.edge_names["subprop"], parent_node)
            
            # Add the node and relationship to the graph
            self.neo4j_graph.merge(parent_node, "ObjectProperty", "name")
            self.neo4j_graph.merge(node, "ObjectProperty", "name")
            self.neo4j_graph.merge(subproperty_relationship)
   


   def add_disjoint_properties(self):
    seen_pairs = set()

    for cls in self.onto.classes():
        for disjoint_axiom in cls.disjoints():
            # disjoint_axiom.entities is the full list of disjoint classes
            classes = list(disjoint_axiom.entities)

            for i in range(len(classes)):
                for j in range(i + 1, len(classes)):
                    cls1 = classes[i]
                    cls2 = classes[j]

                    # Only process if both are named classes (not anonymous restrictions)
                    if not hasattr(cls1, "iri") or not hasattr(cls2, "iri"):
                        continue

                    name1 = self.owl_helper.extract_local_name(cls1.iri)
                    name2 = self.owl_helper.extract_local_name(cls2.iri)

                    # Avoid duplicate edges (unordered pair)
                    if (name1, name2) in seen_pairs or (name2, name1) in seen_pairs:
                        continue

                    seen_pairs.add((name1, name2))

                    node1 = Node("CLASS_PROPERTY", name=name1)
                    node2 = Node("CLASS_PROPERTY", name=name2)
                    disjoint_relationship = Relationship(node1, self.edge_names["disjoint"], node2)

                    self.neo4j_graph.merge(node1, "CLASS_PROPERTY", "name")
                    self.neo4j_graph.merge(node2, "CLASS_PROPERTY", "name")
                    self.neo4j_graph.merge(disjoint_relationship)
            
   def add_all(self):
      self.add_inverse_properties()
      self.add_object_subproperties()
      self.add_transitive_properties()
      self.add_disjoint_properties()

# username = os.getenv("USERNAME_1")
# password = os.getenv("PASSWORD")

# connection = Connector("neo4j", "12345")
# neo4j_graph = connection.connect_neo4j()
# ontology_file = "inputs/PizzaOntology.rdf"

# # Create an instance of GraphMetaData
# onto_metadata = GraphMetaData(ontology_file, neo4j_graph)

# # Test the add_inverse_properties function
# onto_metadata.add_inverse_properties()
# onto_metadata.add_transitive_properties()
# onto_metadata.add_object_subproperties()
      