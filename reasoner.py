from owlready2 import *
import logging
import rdflib
from rdflib.namespace import RDF, RDFS, OWL

# logging.basicConfig(level=logging.DEBUG)


class Reasoner:
   
   def __init__(self, filepath, output_filepath):
      self.filepath = filepath
      self.format = "xml"
      self.output_filepath = output_filepath
      self.onto = get_ontology(self.filepath).load()
      self.rdf_graph = self.load_owl(self.filepath)
   
   def load_owl(self, filename):
      rdf_graph = rdflib.Graph()
      rdf_graph.parse(filename, format=self.format)
      return rdf_graph
         
   def run_reasoner(self):
      with self.onto:
         sync_reasoner()
   
   def reason_subclasses(self):
      
      for cls in self.onto.classes():
         seen = set(cls.INDIRECT_is_a)
         # print(cls)
         to_add = []
         for parent in cls.INDIRECT_is_a:
            if parent != cls and parent not in seen:
               print(f"Inferred: {cls} is a subclass of {parent}")
               to_add.append(parent)
               seen.add(parent)
         cls.is_a.extend(to_add)
         
      def add_classes_to_individuals(self):
         # Adds all the parent classes to the individuals
         for indiv in self.onto.individuals():
            superclasses = indiv.is_a[0].is_a

            to_add = set()
            for cls in superclasses:
               if cls != indiv.is_a[0]:
                  to_add.add(cls)

            indiv.is_a.extend(to_add)

            print(f"Individual: {indiv.name}")
            print(f"Class: {indiv.is_a}")
         
      # add_classes_to_individuals()
   
   def reason_object_properties(self):
      
      # Find reasoning chains for object properties
      property_chain = {}
      for prop in self.onto.object_properties():
         property_chain[prop] = set(prop.is_a)
         
      print(property_chain)
      
      for subj, pred, obj in self.rdf_graph.triples((None, None, None)):
         print(f"Triple: {subj}, {pred}, {obj}")
         print(f"RDF Types: subj={subj.n3(self.rdf_graph.namespace_manager)}, pred={pred.n3(self.rdf_graph.namespace_manager)}, obj={obj.n3(self.rdf_graph.namespace_manager)}")
      
      
      
      
      # for sub, pred, obj in current_result_set:
      #    print(sub, pred, obj)
      #    chain = property_chain.get(pred, [])
      #    print("Chain:", chain)
      #    for link in chain:
      #       for sub1, pred1, obj1 in current_result_set:
      #          if pred1 == link and (sub, pred1, obj1) not in current_result_set:
      #             print(f"New triple found: ({sub}, {pred1}, {obj1})")
      #             setattr(sub, pred1.name, obj1)
                  
      # for indiv in self.onto.individuals():
         
      #    inferred_properties = list(self.onto.world.sparql(f"""SELECT ?p WHERE {{<{indiv.iri}> ?p ?o .}}"""))
      #    current_properties = []
         
      #    for property in inferred_properties:
      #       if type(property[0]) is str:
      #          for item in property:
      #             current_properties.append(item)
         
      #    current_targets = []
         
      #    for relation in current_properties:
      #       inferred_targets = list(self.onto.world.sparql(f"""SELECT ?o WHERE {{<{indiv.iri}> <{relation}> ?o .}}"""))
      #       for item in inferred_targets[0]:                
      #          current_targets.append(item)
         
      #    print(indiv, current_properties, current_targets)
         
      #    result_set = list(self.onto.world.sparql("""SELECT ?s ?p ?o WHERE {?s ?p ?o .}"""))
                  
      #    for prop in current_properties:
      #       for target in current_targets:
      #          triplet = [indiv, prop, target]
      #          if triplet not in result_set:
      #             print("----NEW TRIPLE----", triplet)
      #             setattr(indiv, prop, target)
   
   def save_ontology(self):
      self.onto.save(file=self.output_filepath, format="rdfxml")
      print(f"Ontology saved to {self.output_filepath}")
   

test =  Reasoner("example3.owl", "output_alice.owl")
test.run_reasoner()
print("*******Reasoner finished********")
test.reason_subclasses()
print("*******Subclasses finished********")
test.reason_object_properties()
print("*******Object properties finished********")
test.save_ontology()
print("*******Ontology saved********")



      