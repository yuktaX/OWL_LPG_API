from owlready2 import *
from py2neo import Graph as NeoGraph, Node, Relationship
from Connector import Connector
from OWLhelper import OWLhelper
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Mapper:
   def __init__(self, neo4j_graph, filename, format):

      self.neo4j_graph = neo4j_graph
      self.owl_helper = OWLhelper(filename, format)
      self.onto = self.owl_helper.load_owl_ontology()

   def process_classes(self,nodes):
      for cls in self.onto.classes():
         # Extract the local name of the class (excluding the URI base)
         class_name = self.owl_helper.extract_local_name(cls.iri)
         
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
               subclass_name = self.owl_helper.extract_local_name(subclass.iri)
               superclass_name = self.owl_helper.extract_local_name(superclass.iri)
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

               domain_classes = []
               # Extract the local names for range class
               
               range_name = self.owl_helper.extract_local_name(range_class.iri)
               # Fetch or create the range class node
               range_node = nodes.get(range_class.iri)
               if not range_node:
                     range_node = Node("Class", name=range_name)
                     self.neo4j_graph.merge(range_node)
                     nodes[range_class.iri] = range_node  # Add to nodes dictionary
               domain_classes = list(domain_class.subclasses())  # make a copy
               if domain_class not in domain_classes:
                     domain_classes.append(domain_class)
               
               #recursively get the subclass tree and add to a the list domain_classes
               self.owl_helper.recAddSubClass(domain_class,domain_classes)

               range_classes = []
               range_classes.append(range_class)
               self.owl_helper.recAddSuperClass(range_class,range_classes)


               for d_cls in domain_classes:
                     for r_cls in range_classes:
                        
                        if isinstance(d_cls,Restriction):    #remove the cls != domain_class if you want all sub classes to also be considered
                           continue
                        d_cls_name = self.owl_helper.extract_local_name(d_cls.iri)
                        # Fetch or create the domain class node
                        d_cls_node = nodes.get(d_cls.iri)
                        if not d_cls_node:
                           d_cls_node = Node("Class", name=d_cls_name)
                           self.neo4j_graph.merge(d_cls_node)
                           nodes[d_cls.iri] = d_cls_node  # Add to nodes dictionary

                        if isinstance(r_cls,Restriction):    #remove the cls != domain_class if you want all sub classes to also be considered
                           continue
                        r_cls_name = self.owl_helper.extract_local_name(r_cls.iri)
                        # Fetch or create the domain class node
                        r_cls_node = nodes.get(r_cls.iri)
                        if not r_cls_node:
                           r_cls_node = Node("Class", name=r_cls_name)
                           self.neo4j_graph.create(r_cls_node)
                           nodes[r_cls.iri] = r_cls_node  # Add to nodes dictionary
                           
                        # Create a relationship between the domain (or domain subclass) and range using the property name
                        rel = Relationship(d_cls_node, prop_name.upper(), r_cls_node)
                        self.neo4j_graph.create(rel)
                        
                        # print(f"Creating Relationship: {cls_node} --{prop_name.upper()}--> {range_name}")
                        for ancestor_prop in prop.is_a:
                           if isinstance(ancestor_prop, ObjectPropertyClass) and ancestor_prop != prop:
                              rel_name = ancestor_prop.name
                              relationship = Relationship(d_cls_node, rel_name.upper(), r_cls_node)
                              # print(f"Creating inferred relationship: {cls.name} --{rel_name}--> {range_class.name}")
                              self.neo4j_graph.merge(relationship)
               
               
         #go through all the instances, check what their parents are and assign all object propeties of their parents to the instance
         for indi in self.onto.individuals():

            individual_name = self.owl_helper.extract_local_name(indi.iri)
            print("indi name")
            print(individual_name)

            individual_node = nodes.get(indi.iri)
            if not individual_node:
               individual_node = Node("Individual", name=individual_name)
               self.neo4j_graph.merge(individual_node)
               nodes[indi.iri] = individual_node  # Add to nodes dictionary

            instance_rel = list(self.neo4j_graph.match((individual_node,), r_type="INSTANCE_OF"))
            for rel in instance_rel:
                  print("--------------------in---------------------------------------")
                  class_node = rel.end_node  # This is the class the individual belongs tocreate
                  print(class_node)

                  # Now, fetch all *outgoing* relationships from the class node (except INSTANCE_OF)
                  class_rels = self.neo4j_graph.match((class_node,), r_type=None)
                  for class_rel in class_rels:
                     print("class_rel.__class__.__name__")
                     print(class_rel.__class__.__name__)
                     if class_rel.__class__.__name__ == "Relationship":
                        continue
                     if class_rel.__class__ == Relationship:
                        continue
                     if class_rel.type == "INSTANCE_OF":
                        continue  # Skip INSTANCE_OF
                     
                     if class_rel.__class__.__name__ == "HASTOPPING":
                         print()
                         print("HASTOPPING yeah")
                         print(class_rel.end_node['name'])
                         print()
                     print("class_rel")
                     print(class_rel.end_node)
                     # Copy the same relationship to the individual node
                     new_rel = Relationship(individual_node, class_rel.__class__.__name__, class_rel.end_node)
                     self.neo4j_graph.merge(new_rel)
                     print(f"Copied relationship: {individual_node['name']} --{class_rel.__class__.__name__}--> {class_rel.end_node['name']}")
                   
               
   def process_equivalent_class_intersections(self,nodes):
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
                                 
                                 cls_node = nodes.get(cls.iri)
                                 if not cls_node:
                                    cls_node = Node("Class", name=cls_name)
                                    self.neo4j_graph.merge(cls_node,"Class","name")
                                    nodes[cls.iri] = cls_node
                                 self.neo4j_graph.create(Relationship(cls_node,
                                                                  f"{prop_name.upper()}",
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
                                                   f"{prop_name.upper()}",
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
               domain_name = self.owl_helper.extract_local_name(domain_class.iri)
               range_name = self.owl_helper.extract_local_name(range_class.iri)

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
                     domain_name = self.owl_helper.extract_local_name(domain_class.iri)
                     range_name = self.owl_helper.extract_local_name(range_class.iri)
                     
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
   
   def process_individuals(self, nodes):
    for individual in self.onto.individuals():
        # Extract the local name of the individual
        individual_name = self.owl_helper.extract_local_name(individual.iri)

        # Create a Neo4j node for this individual
      #   individual_node = Node("Individual", name=individual_name)
        individual_node = nodes.get(individual.iri)
        if not individual_node:
            individual_node = Node("Individual", name=individual_name)
            self.neo4j_graph.create(individual_node)
            nodes[individual.iri] = individual_node  # Add to nodes dictionary

      #   self.neo4j_graph.merge(individual_node, "Individual", "name")

        # Attach INSTANCE_OF relationship to class
        for cls in individual.is_a:
            if cls in self.onto.classes():
                class_name = self.owl_helper.extract_local_name(cls.iri)

                # Use or create class node
                class_node = nodes.get(cls.iri)
                if not class_node:
                    class_node = Node("Class", name=class_name)
                    self.neo4j_graph.merge(class_node, "Class", "name")
                    nodes[cls.iri] = class_node

                # Create INSTANCE_OF relationship
                rel = Relationship(individual_node, "INSTANCE_OF", class_node)
                self.neo4j_graph.merge(rel)
                print(f"Creating INSTANCE_OF: {individual_name} --> {class_name}")

        # Process properties (object and data)
        for prop in individual.get_properties():
            for value in prop[individual]:
                if isinstance(value, Thing):  # Object property
                    target_name = self.owl_helper.extract_local_name(value.iri)
                    target_node = Node("Individual", name=target_name)
                    self.neo4j_graph.merge(target_node, "Individual", "name")

                    rel = Relationship(individual_node, prop.name.upper(), target_node)
                    self.neo4j_graph.merge(rel)
                    print(f"Creating object property: {individual_name} --{prop.name.upper()}--> {target_name}")

                elif isinstance(value, (str, int, float, bool)):  # Data property
                    individual_node[prop.name] = value
                    self.neo4j_graph.push(individual_node)

   def process_transitive_properties(self, nodes):
      for individual in self.onto.individuals():
         for prop in self.onto.object_properties():
            indirect_prop_name = f"INDIRECT_{prop.name}"
            
            related_ind = getattr(individual, indirect_prop_name)
            print(f"Individual name: {individual.name}, Property name: {prop.name}")

            if not related_ind == []:
               print(related_ind)

               ind_name = self.extract_local_name(individual.iri)
               # Fetch or create the range class node
               ind_node = nodes.get(individual.iri)
               # if not ind_node:
               #       print("No ind")
               #       ind_node = Node("Individual", name=ind_name)
               #       self.neo4j_graph.merge(ind_node)
               #       nodes[individual.iri] = ind_node  # Add to nodes dictionary
               
               for obj in related_ind:
                  obj_name = self.extract_local_name(obj.iri)
                  obj_node = nodes.get(obj.iri)
                  # if not obj_node:
                  #    print("No obj")
                  #    obj_node = Node("Class", name=obj_name)
                  #    self.neo4j_graph.create(obj_node)
                  #    nodes[obj.iri] = obj_node  # Add to nodes dictionary
                  
                  print("Creating relationship")
                  rel = Relationship(ind_node, prop.name.upper(), obj_node)
                  self.neo4j_graph.merge(rel)

   def map_owl_to_lpg(self):

      # Store nodes for individuals and classes
      nodes = {}
      
      # Step 1: Process OWL Classes and Create LPG Nodes
      self.process_classes(nodes)
      
      # Step 2: Process Subclass Relationships
      self.process_subclass_relationships(nodes)

      # Step 3: Process individuals
      self.process_individuals(nodes)

      # Step 4: Process Object Properties (Relationships)
      self.process_object_properties(nodes)

      # Step 5: Process equivalent classes
      self.process_equivalent_class_intersections(nodes)
      
      # Step 6: Process inverse object properties
      self.process_inverse_object_properties(nodes)
      
      # Step 7: Process object subproperties
      self.process_object_subproperties(nodes)

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

filename = "examples/example4.owl"

test = Mapper(neo4j_graph, filename, format)

test.map_owl_to_lpg()


