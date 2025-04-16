import rdflib
import logging
from rdflib import URIRef
# from owlready2 import get_ontology, ObjectPropertyClass,DataPropertyClass,Restriction,ThingClass
from owlready2 import *

# logging.basicConfig(level=logging.DEBUG)
from py2neo import Graph as NeoGraph, Node, Relationship
from rdflib.namespace import RDF, RDFS, OWL
from rdflib.term import Literal

username = "neo4j"  #put your own neo4j username here
password = "12345"  #put your own password here
format = "xml"

class Mapper:
   def __init__(self, username, password, filename,format="xml"):
      self.username = username
      self.password = password
      self.format = format
      self.neo4j_graph = None
      self.filename = filename
      self.onto = get_ontology(filename).load()

   def connect_neo4j(self):
      self.neo4j_graph = NeoGraph("bolt://localhost:7687", auth=(self.username, self.password))
      return self.neo4j_graph

   def load_owl(self):
      rdf_graph = rdflib.Graph()
      rdf_graph.parse(self.filename, format=self.format)
      return rdf_graph
    
   def extract_local_name(self,uri):
      uri = str(uri)
      if "#" in uri:
          return uri.split("#")[-1]
      elif "/" in uri:
          return uri.split("/")[-1]
      elif ":" in uri:
          return uri.split(":")[-1]
      else:
          return uri
    

   def process_classes(self,nodes):
      for cls in self.onto.classes():
         # Extract the local name of the class (excluding the URI base)
         class_name = self.extract_local_name(cls.iri)
         
         # Create a Neo4j node for this class
         class_node = Node("Class", name=class_name)
         # Add to Neo4j graph (create if not exists)
         self.neo4j_graph.create(class_node)
         # print("-------------------------------------------------------")
         # print(cls.iri)
         nodes[cls.iri] = class_node
          
   def process_subclass_relationships(self,nodes):
      for subclass in self.onto.classes():
         # Iterate over all superclasses (is_a relationships)
         for superclass in subclass.is_a:
            if superclass in self.onto.classes():  # Ensure the superclass is a valid class
               # Extract the local names of the subclass and superclass
               subclass_name = self.extract_local_name(subclass.iri)
               superclass_name = self.extract_local_name(superclass.iri)
               # Fetch or create the nodes for subclass and superclass
               subclass_node = nodes.get(subclass.iri)  # Using the existing node for the subclass
               superclass_node = nodes.get(superclass.iri)  # Using the existing node for the superclass
               if not subclass_node:
                     subclass_node = Node("Class", name=subclass_name)
                     self.neo4j_graph.create(subclass_node)
                     nodes[subclass.iri] = subclass_node  # Add to nodes dictionary
               
               if not superclass_node:
                     superclass_node = Node("Class", name=superclass_name)
                     self.neo4j_graph.create(superclass_node)
                     nodes[superclass.iri] = superclass_node  # Add to nodes dictionary
               # Create a relationship between subclass and superclass (if not already created)
               rel = Relationship(subclass_node, "SUBCLASS_OF", superclass_node)
               self.neo4j_graph.create(rel)
               print(f"Creating SUBCLASS_OF: {subclass_name} --> {superclass_name}")
            else:
               print(f"Skipping subclass relation: {subclass} ⊆ {superclass} (invalid superclass)")

   def process_object_properties(self,nodes):
      for prop in self.onto.object_properties():
         # Extract the property name
         prop_name = prop.name
         # Iterate through the domain and range of the object property
         for domain_class in prop.domain:
            for range_class in prop.range:
               # Extract the local names for range class
               
               range_name = self.extract_local_name(range_class.iri)
               # Fetch or create the range class node
               range_node = nodes.get(range_class.iri)
               if not range_node:
                     range_node = Node("Class", name=range_name)
                     self.neo4j_graph.create(range_node)
                     nodes[range_class.iri] = range_node  # Add to nodes dictionary
               domain_classes = list(domain_class.subclasses())  # make a copy
               if domain_class not in domain_classes:
                     domain_classes.append(domain_class)
   
               for cls in domain_classes:
                     if isinstance(cls,Restriction) or cls != domain_class:    #remove the cls != domain_class if you want all sub classes to also be considered
                        continue
                     cls_name = self.extract_local_name(cls.iri)
                     # Fetch or create the domain class node
                     cls_node = nodes.get(cls.iri)
                     if not cls_node:
                        cls_node = Node("Class", name=cls_name)
                        self.neo4j_graph.create(cls_node)
                        nodes[cls.iri] = cls_node  # Add to nodes dictionary
                        
                     # Create a relationship between the domain (or domain subclass) and range using the property name
                     rel = Relationship(cls_node, prop_name.upper(), range_node)
                     self.neo4j_graph.create(rel)
                     
                     # print(f"Creating Relationship: {cls_node} --{prop_name.upper()}--> {range_name}")
                     for ancestor_prop in prop.is_a:
                        if isinstance(ancestor_prop, ObjectPropertyClass) and ancestor_prop != prop:
                           rel_name = ancestor_prop.name
                           relationship = Relationship(cls_node, rel_name.upper(), range_node)
                           # print(f"Creating inferred relationship: {cls.name} --{rel_name}--> {range_class.name}")
                           self.neo4j_graph.merge(relationship)
                              
   def process_individuals(self, nodes):
      
         for individual in self.onto.individuals():
               # Extract the local name of the individual (excluding the URI base)
               individual_name = self.extract_local_name(individual.iri)

               # Create a Neo4j node for this individual
               individual_node = Node("Individual", name=individual_name)

               # Add to Neo4j graph (create if not exists)
               self.neo4j_graph.create(individual_node)

               # Find the class the individual is an instance of (i.e., the class it belongs to)
               for cls in individual.is_a:
                  if cls in self.onto.classes():  # Ensure the class is valid
                     # Extract the class name and create a relationship between individual and class
                     class_name = self.extract_local_name(cls.iri)

                     # Fetch or create the class node
                     class_node = nodes.get(cls.iri)  # Using the existing node for the class
                     if not class_node:
                           class_node = Node("Class", name=class_name)
                           self.neo4j_graph.create(class_node)
                           nodes[cls.iri] = class_node  # Add to nodes dictionary

                     # Create a relationship between the individual and the class (e.g., "INSTANCE_OF")
                     rel = Relationship(individual_node, "INSTANCE_OF", class_node)
                     self.neo4j_graph.merge(rel)
                     print(f"Creating INSTANCE_OF: {individual_name} --> {class_name}")

                  # Process relationships between individuals
                  inferred_properties = list(self.onto.world.sparql(f"""SELECT ?p WHERE {{<{individual.iri}> ?p ?o .}}"""))
                  print(inferred_properties)
                  for property in inferred_properties:
                     prop_iri = property[0]
                     if isinstance(prop_iri, URIRef):  # Ensure it's a valid property URI
                        prop_name = self.extract_local_name(prop_iri)
                        inferred_targets = list(self.onto.world.sparql(f"""SELECT ?o WHERE {{<{individual.iri}> <{prop_iri}> ?o .}}"""))
                        for target in inferred_targets:
                           
                           target_iri = target[0]
                           if isinstance(target_iri, URIRef):  # Ensure the target is a valid URI
                              target_name = self.extract_local_name(target_iri)

                              # Fetch or create the target individual node
                              target_node = Node("Individual", name=target_name)
                              self.neo4j_graph.merge(target_node, "Individual", "name")

                              # Create a relationship between the individuals
                              rel = Relationship(individual_node, prop_name.upper(), target_node)
                              self.neo4j_graph.merge(rel)
                              print(f"Creating Relationship: {individual_name} --{prop_name.upper()}--> {target_name}")
       
   def process_equivalent_class_intersections(self):
      for cls in self.onto.classes():
         for eq in cls.equivalent_to:
               if isinstance(eq, And):
                  for part in eq.Classes:
                     if isinstance(part, ThingClass):
                           # It's a base class (like Pizza)
                           start_node = Node("Class", name=self.extract_local_name(cls.iri))
                           end_node = Node("Class", name=self.extract_local_name(part.iri))
                           self.neo4j_graph.merge(start_node,"Class","name")
                           self.neo4j_graph.merge(end_node,"Class","name")

                           rel = Relationship(start_node,
                                          "EQUIVALENT_TO",
                                          end_node)
                           self.neo4j_graph.merge(rel)
                     elif isinstance(part, Restriction):
                           prop_name = part.property.name
                           filler = part.value

                           restriction_id = f"{cls.name}_{prop_name}_{str(filler)}"
                           restriction_node = Node("Restriction", type="some", id=restriction_id)
                           self.neo4j_graph.merge(restriction_node, "Restriction", "id")

                           start_node = Node("Class", name=self.extract_local_name(cls.iri))
                           self.neo4j_graph.merge(start_node, "Class", "name")

                           # From class to restriction
                           self.neo4j_graph.merge(Relationship(start_node),
                                                   "RESTRICTION", restriction_node)

                           # Property node
                           prop_node = Node("Property", name=prop_name)
                           self.neo4j_graph.merge(prop_node,"Class","name")

                           self.neo4j_graph.merge(Relationship(restriction_node, "ON_PROPERTY", prop_node))

                           # Filler class (e.g., CheeseTopping)
                           if isinstance(filler, ThingClass):
                              filler_node = Node("Class", name=self.extract_local_name(filler.iri))
                              self.neo4j_graph.merge(filler_node,"Class","name")

                              self.neo4j_graph.merge(Relationship(restriction_node, "SOME_VALUES_FROM", filler_node))

                              # Optional shortcut for querying
                              self.neo4j_graph.create(Relationship(start_node,
                                                                  f"{prop_name.upper()}_SOME",
                                                                  filler_node))
                           elif isinstance(filler, ConstrainedDatatype):
                              filler_node = Node("Datatype", name=str(filler))
                              self.neo4j_graph.merge(filler_node,"Class","name")
                              self.neo4j_graph.merge(Relationship(restriction_node, "SOME_VALUES_FROM", filler_node))
                              print(f"Handled restriction to datatype: {filler}")
                           else:
                              print(f"Unknown filler type: {type(filler)}")

                           self.neo4j_graph.merge(Relationship(restriction_node, "SOME_VALUES_FROM", filler_node))

                           # Optional shortcut
                           self.neo4j_graph.merge(Relationship(start_node,
                                                   f"{prop_name.upper()}_SOME",
                                                   filler_node))
                           
   def process_inverse_object_properties(self, nodes):
      for prop in self.onto.object_properties():
         # Check if the property has an inverse
         if prop.inverse_property:
            inverse_prop = prop.inverse_property
            inverse_name = inverse_prop.name
         else:
            continue
            
         print(f"Processing inverse property: {inverse_name}")

         # Iterate through the domain and range of the object property
         for domain_class in prop.domain:
            for range_class in prop.range:
            # Extract the local names for domain and range classes
               domain_name = self.extract_local_name(domain_class.iri)
               range_name = self.extract_local_name(range_class.iri)

               # Fetch or create the domain and range class nodes
               domain_node = nodes.get(domain_class.iri)
               if not domain_node:
                  domain_node = Node("Class", name=domain_name)
                  self.neo4j_graph.create(domain_node)
                  nodes[domain_class.iri] = domain_node

               range_node = nodes.get(range_class.iri)
               if not range_node:
                  range_node = Node("Class", name=range_name)
                  self.neo4j_graph.create(range_node)
                  nodes[range_class.iri] = range_node

               # Create a relationship for the inverse property
               rel = Relationship(range_node, inverse_name.upper(), domain_node)
               self.neo4j_graph.merge(rel)
               print(f"Creating INVERSE Relationship: {range_name} --{inverse_name.upper()}--> {domain_name}")
               
   def process_object_subproperties(self, nodes):
      for prop in self.onto.object_properties():
         # Check if the property has a superproperty (subPropertyOf relationship)
         for superprop in prop.is_a:
            if isinstance(superprop, ObjectPropertyClass):
               prop_name = prop.name
               superprop_name = superprop.name
               print(f"Processing subproperty: {prop_name} ⊆ {superprop_name}")

               # Iterate through the domain and range of the object property
               for domain_class in prop.domain:
                  for range_class in prop.range:
                     # Extract the local names for domain and range classes
                     domain_name = self.extract_local_name(domain_class.iri)
                     range_name = self.extract_local_name(range_class.iri)
                     
                     # print(domain_name, range_name)

                     # Fetch or create the domain and range class nodes
                     domain_node = nodes.get(domain_class.iri)
                     if not domain_node:
                        domain_node = Node("Class", name=domain_name)
                        self.neo4j_graph.create(domain_node)
                        nodes[domain_class.iri] = domain_node

                     range_node = nodes.get(range_class.iri)
                     if not range_node:
                        range_node = Node("Class", name=range_name)
                        self.neo4j_graph.create(range_node)
                        nodes[range_class.iri] = range_node

                     # Create a relationship for the superproperty
                     rel = Relationship(domain_node, superprop_name.upper(), range_node)
                     self.neo4j_graph.merge(rel)
                     print(f"Creating SUBPROPERTY_OF Relationship: {domain_name} --{superprop_name.upper()}--> {range_name}")
      
   def map_owl_to_lpg(self):
      # Connect to Neo4j and clear the database
      self.connect_neo4j()
      self.neo4j_graph.delete_all()

      # Store nodes for individuals and classes
      nodes = {}
      
      # Step 1: Process OWL Classes and Create LPG Nodes
      self.process_classes(nodes)
      
      # Step 2: Process Subclass Relationships
      self.process_subclass_relationships(nodes)
      
      # Step 3: Process Object Properties (Relationships)
      self.process_object_properties(nodes)
            
      # Step 4: Process Individuals and Create Nodes
      self.process_individuals(nodes)

      # Step 5: Process equivalent classes
      self.process_equivalent_class_intersections()
      
      # Step 6: Process inverse object properties
      self.process_inverse_object_properties(nodes)
      
      # Step 7: Process object subproperties
      self.process_object_subproperties(nodes)

      print("OWL to LPG Conversion Complete!")


filename = "output_pizza_new.owl"
# test = Mapper(username, password, "PizzaOntology.rdf", format)
# test = Mapper(username, password, "example4.owl", format)
test = Mapper(username, password, filename, format)
test.map_owl_to_lpg()


