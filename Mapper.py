from owlready2 import *
from py2neo import Graph as NeoGraph, Node, Relationship
from Connector import Connector
from OWLHelper import OWLHelper
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Mapper:
   
   def __init__(self, neo4j_graph, filename, format):

      self.neo4j_graph = neo4j_graph
      self.owl_helper = OWLHelper(filename, format)
      self.onto = self.owl_helper.load_owl_ontology()
      self.nodes = {}

   def process_classes(self):
      
      for cls in self.onto.classes():
         class_name = self.owl_helper.extract_local_name(cls.iri)
         
         # Create a Neo4j node for this class and add it to graph it if it doesn't exist
         class_node = Node("Class", name=class_name)
         self.neo4j_graph.create(class_node)
         self.nodes[cls.iri] = class_node
          
   def process_subclass_relationships(self):
      
      for subclass in self.onto.classes():
         for superclass in subclass.is_a:    # Iterate over all superclasses (is_a relationships)
            if superclass in self.onto.classes():  # Ensure the superclass is a valid class
               
               # Extract the local names of the subclass and superclass
               subclass_name = self.owl_helper.extract_local_name(subclass.iri)
               superclass_name = self.owl_helper.extract_local_name(superclass.iri)
               
               # Fetch or create the self.nodes for subclass and superclass
               subclass_node = self.nodes.get(subclass.iri)  # Using the existing node for the subclass
               superclass_node = self.nodes.get(superclass.iri)  # Using the existing node for the superclass
               
               if not subclass_node:
                     subclass_node = Node("Class", name=subclass_name)
                     self.neo4j_graph.create(subclass_node)
                     self.nodes[subclass.iri] = subclass_node
               
               if not superclass_node:
                     superclass_node = Node("Class", name=superclass_name)
                     self.neo4j_graph.create(superclass_node)
                     self.nodes[superclass.iri] = superclass_node  
                     
               # Create a relationship between subclass and superclass (if not already created)
               rel = Relationship(subclass_node, "SUBCLASS_OF", superclass_node)
               self.neo4j_graph.merge(rel)
               print(f"Creating SUBCLASS_OF: {subclass_name} --> {superclass_name}")
               
            # else: #here superclass is "THing"
            #    print(f"Skipping subclass relation: {subclass} ⊆ {superclass} (invalid superclass)")

   def process_object_properties(self):
      
      for prop in self.onto.object_properties():
         prop_name = prop.name
         
         # Iterate through the domain and range of the object property
         for domain_class in prop.domain:
            for range_class in prop.range:
               
               # Extract the local names for range class
               range_name = self.owl_helper.extract_local_name(range_class.iri)
               # Fetch or create the range class node
               range_node = self.nodes.get(range_class.iri)
               
               if not range_node:
                     range_node = Node("Class", name=range_name)
                     self.neo4j_graph.merge(range_node)
                     self.nodes[range_class.iri] = range_node  # Add to self.nodes dictionary
               
               d_cls, r_cls = domain_class, range_class
               
               if isinstance(d_cls,Restriction) or isinstance(r_cls,Restriction):    #remove the cls != domain_class if you want all sub classes to also be considered
                     continue
               
               d_cls_name = self.owl_helper.extract_local_name(d_cls.iri)
               r_cls_name = self.owl_helper.extract_local_name(r_cls.iri)
               
               # Fetch or create the domain class node
               d_cls_node = self.nodes.get(d_cls.iri)
               if not d_cls_node:
                  d_cls_node = Node("Class", name=d_cls_name)
                  self.neo4j_graph.merge(d_cls_node)
                  self.nodes[d_cls.iri] = d_cls_node  

               # Fetch or create the range class node
               r_cls_node = self.nodes.get(r_cls.iri)
               if not r_cls_node:
                  r_cls_node = Node("Class", name=r_cls_name)
                  self.neo4j_graph.create(r_cls_node)
                  self.nodes[r_cls.iri] = r_cls_node  
                  
               # Create a relationship between the domain (or domain subclass) and range using the property name
               print(f"Creating Relationship: {d_cls_name} --{prop_name.upper()}--> {r_cls_name}")
               rel = Relationship(d_cls_node, prop_name.upper(), r_cls_node)
               self.neo4j_graph.merge(rel)
               
               #add all the ancestor properties to the relationship
               for ancestor_prop in prop.is_a:
                  if isinstance(ancestor_prop, ObjectPropertyClass) and ancestor_prop != prop and ancestor_prop != prop and ancestor_prop.name.upper() != "OBJECTPROPERTY":
                     rel_name = ancestor_prop.name
                     relationship = Relationship(d_cls_node, rel_name.upper(), r_cls_node)
                     print(f"Creating inferred relationship: {d_cls_node} --{rel_name}--> {range_class.name}")
                     self.neo4j_graph.merge(relationship)
               
         #go through all the instances, check what their parents are and assign all object propeties of their parents to the instance
         for indi in self.onto.individuals():
            individual_name = self.owl_helper.extract_local_name(indi.iri)
            print(f"Processing individual: {individual_name}")

            # Fetch or create the individual node
            individual_node = self.nodes.get(indi.iri)
            if not individual_node:
               individual_node = Node("Individual", name=individual_name)
               self.neo4j_graph.merge(individual_node)
               self.nodes[indi.iri] = individual_node

            # Find INSTANCE_OF relationships for the individual
            instance_rels = list(self.neo4j_graph.match((individual_node,), r_type="INSTANCE_OF"))
            for rel in instance_rels:
               class_node = rel.end_node  # Class node the individual belongs to
               print(f"Found INSTANCE_OF relationship: {individual_name} --> {class_node['name']}")

               # Fetch all outgoing relationships from the class node (excluding INSTANCE_OF)
               class_rels = self.neo4j_graph.match((class_node,), r_type=None)
               for class_rel in class_rels:
                  if class_rel.type == "INSTANCE_OF" or class_rel.__class__.__name__ == "Relationship" or class_rel.__class__ == Relationship:
                     continue  # Skip INSTANCE_OF relationships

                  # Copy the relationship to the individual node
                  new_rel = Relationship(individual_node, class_rel.__class__.__name__, class_rel.end_node)
                  self.neo4j_graph.merge(new_rel)
                  print(f"Copied relationship: {individual_name} --{class_rel.__class__.__name__}--> {class_rel.end_node['name']}")

   def process_equivalent_class_intersections(self):
      for cls in self.onto.classes():
         for eq in cls.equivalent_to:
               if isinstance(eq, And):
                  for part in eq.Classes:
                     if isinstance(part, ThingClass):
                           # It's a base class (like Pizza)
                           start_node = Node("Class", name=self.owl_helper.extract_local_name(cls.iri))
                           end_node = Node("Class", name=self.owl_helper.extract_local_name(part.iri))
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

                           start_node = Node("Class", name=self.owl_helper.extract_local_name(cls.iri))
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
                              filler_node = Node("Class", name=self.owl_helper.extract_local_name(filler.iri))
                              self.neo4j_graph.merge(filler_node,"Class","name")

                              self.neo4j_graph.merge(Relationship(restriction_node, "SOME_VALUES_FROM", filler_node))

                              # # Optional shortcut for querying
                              # self.neo4j_graph.create(Relationship(start_node,
                              #                                     f"{prop_name.upper()}",
                              #                                     filler_node))
                              subclasses = []
                              self.owl_helper.recAddSubClass(cls,subclasses)

                              for cls in subclasses:
                                 cls_name = self.owl_helper.extract_local_name(cls.iri)
                                 
                                 cls_node = self.nodes.get(cls.iri)
                                 if not cls_node:
                                    cls_node = Node("Class", name=cls_name)
                                    self.neo4j_graph.merge(cls_node,"Class","name")
                                    self.nodes[cls.iri] = cls_node
                                 self.neo4j_graph.create(Relationship(cls_node,
                                                                  f"{prop_name.upper()}",
                                                                  filler_node))

                           elif isinstance(filler, ConstrainedDatatype):
                              filler_node = Node("Datatype", name=str(filler))
                              self.neo4j_graph.merge(filler_node,"Datatype","name")
                              self.neo4j_graph.merge(Relationship(restriction_node, "SOME_VALUES_FROM", filler_node))
                              print(f"Handled restriction to datatype: {filler}")
                           else:
                              print(f"Unknown filler type: {type(filler)}")

                           self.neo4j_graph.merge(Relationship(restriction_node, "SOME_VALUES_FROM", filler_node))

                           # Optional shortcut
                           self.neo4j_graph.merge(Relationship(start_node,
                                                   f"{prop_name.upper()}",
                                                   filler_node))
           
   def process_inverse_object_properties(self):
      
      for prop in self.onto.object_properties():
         
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
               domain_name = self.owl_helper.extract_local_name(domain_class.iri)
               range_name = self.owl_helper.extract_local_name(range_class.iri)

               # Fetch or create the domain and range class self.nodes
               domain_node = self.nodes.get(domain_class.iri)
               if not domain_node:
                  domain_node = Node("Class", name=domain_name)
                  self.neo4j_graph.create(domain_node)
                  self.nodes[domain_class.iri] = domain_node

               range_node = self.nodes.get(range_class.iri)
               if not range_node:
                  range_node = Node("Class", name=range_name)
                  self.neo4j_graph.create(range_node)
                  self.nodes[range_class.iri] = range_node

               # Create a relationship for the inverse property
               rel = Relationship(range_node, inverse_name.upper(), domain_node)
               self.neo4j_graph.merge(rel)
               print(f"Creating INVERSE Relationship: {range_name} --{inverse_name.upper()}--> {domain_name}")
               
   def process_object_subproperties(self):
      
      for prop in self.onto.object_properties():
         
         # Check if the property has a superproperty (subPropertyOf relationship)
         for superprop in prop.is_a:
            
            if isinstance(superprop, ObjectPropertyClass) and superprop != prop and superprop.name.upper() != "OBJECTPROPERTY":
               prop_name = prop.name
               superprop_name = superprop.name
               print(f"Processing subproperty: {prop_name} ⊆ {superprop_name}")

               # Iterate through the domain and range of the object property
               for domain_class in prop.domain:
                  for range_class in prop.range:
                     
                     # Extract the local names for domain and range classes
                     domain_name = self.owl_helper.extract_local_name(domain_class.iri)
                     range_name = self.owl_helper.extract_local_name(range_class.iri)

                     # Fetch or create the domain and range class self.nodes
                     domain_node = self.nodes.get(domain_class.iri)
                     if not domain_node:
                        domain_node = Node("Class", name=domain_name)
                        self.neo4j_graph.create(domain_node)
                        self.nodes[domain_class.iri] = domain_node

                     range_node = self.nodes.get(range_class.iri)
                     if not range_node:
                        range_node = Node("Class", name=range_name)
                        self.neo4j_graph.create(range_node)
                        self.nodes[range_class.iri] = range_node

                     # Create a relationship for the superproperty
                     rel = Relationship(domain_node, superprop_name.upper(), range_node)
                     self.neo4j_graph.merge(rel)
                     print(f"Creating SUBPROPERTY_OF Relationship: {domain_name} --{superprop_name.upper()}--> {range_name}")
   
   def process_individuals(self):
      
    for individual in self.onto.individuals():

        individual_name = self.owl_helper.extract_local_name(individual.iri)

        # Create a Neo4j node for this individual
        individual_node = self.nodes.get(individual.iri)
        if not individual_node:
            individual_node = Node("Individual", name=individual_name)
            self.neo4j_graph.create(individual_node)
            self.nodes[individual.iri] = individual_node 

        # Process class/subclass relationships
        for cls in individual.is_a:
            if cls in self.onto.classes():
               class_name = self.owl_helper.extract_local_name(cls.iri)

               # Use or create class node
               class_node = self.nodes.get(cls.iri)
               if not class_node:
                  class_node = Node("Class", name=class_name)
                  self.neo4j_graph.merge(class_node, "Class", "name")
                  self.nodes[cls.iri] = class_node

               # Create INSTANCE_OF relationship
               rel = Relationship(individual_node, "INSTANCE_OF", class_node)
               self.neo4j_graph.merge(rel)
               print(f"Creating INSTANCE_OF: {individual_name} --> {class_name}")

        # Process properties (object and data)
        for prop in individual.get_properties():
         # A property can have multiple values\individuals
            for value in prop[individual]:
                  # Check if value is another OWL individual and add the relationship
                  if isinstance(value, Thing): 
                     target_name = self.owl_helper.extract_local_name(value.iri)
                     target_node = Node("Individual", name = target_name)
                     self.neo4j_graph.merge(target_node, "Individual", "name")

                     rel = Relationship(individual_node, prop.name.upper(), target_node)
                     self.neo4j_graph.merge(rel)
                     print(f"Creating object property: {individual_name} --{prop.name.upper()}--> {target_name}")

                  # If Data property, set it on node
                  elif isinstance(value, (str, int, float, bool)):  
                     individual_node[prop.name] = value
                     self.neo4j_graph.push(individual_node)

   def process_transitive_properties(self):
      
      for individual in self.onto.individuals():
         for prop in self.onto.object_properties():
            
            # Check if the property is transitive and get all related edges
            indirect_prop_name = f"INDIRECT_{prop.name}"
            related_ind = getattr(individual, indirect_prop_name)
            print(f"Individual name: {individual.name}, Property name: {prop.name}, Related individuals: {related_ind}")

            for obj in related_ind:
               obj_node = self.nodes.get(obj.iri)
               ind_node = self.nodes.get(individual.iri)
               
               print("Creating TRANSITIVE relationship {} --{}--> {}".format(ind_node, prop.name.upper(), obj_node))
               rel = Relationship(ind_node, prop.name.upper(), obj_node)
               self.neo4j_graph.merge(rel)

   def map_owl_to_lpg(self):
      
      # Step 1: Process OWL Classes and Create LPG Nodes
      self.process_classes()
      
      # Step 2: Process Subclass Relationships
      self.process_subclass_relationships()

      # Step 3: Process individuals
      self.process_individuals()

      # Step 4: Process Object Properties (Relationships)
      self.process_object_properties()

      # Step 5: Process equivalent classes
      self.process_equivalent_class_intersections()
      
      # Step 6: Process inverse object properties
      self.process_inverse_object_properties()
      
      # Step 7: Process object subproperties
      self.process_object_subproperties()

      print("OWL to LPG Conversion Complete!")
      
# Retrieve environment variables
username = os.getenv("USERNAME_1")
password = os.getenv("PASSWORD")


# Check if variables are loaded correctly
if not username or not password:
    raise ValueError("USERNAME or PASSWORD environment variables are not set. Check your .env file.")

format = "xml"
connection = Connector(username, password)
neo4j_graph = connection.connect_neo4j()

filename = "inputs/PizzaOntology.rdf"
# filename = "outputs/output_pizza_new.owl"
# filename = "inputs/animal.owl"


test = Mapper(neo4j_graph, filename, format)

test.map_owl_to_lpg()


