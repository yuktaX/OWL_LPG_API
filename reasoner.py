from owlready2 import *

file_path = "file://PizzaOntologyOWL.owl"

class Reasoner:
   
   def __init__(self, filepath, output_filepath):
      self.filepath = filepath
      self.output_filepath = output_filepath
      
      self.onto = get_ontology(self.filepath).load()
         
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
      
      for indiv in self.onto.individuals():
         superclasses = indiv.is_a[0].is_a

         toAdd = set()
         for cls in superclasses:
            if cls != indiv.is_a[0]:
               toAdd.add(cls)
               
         indiv.is_a.extend(toAdd)
               
         print(f"Individual: {indiv.name}")
         print(f"Class: {indiv.is_a}")
   
   def save_ontology(self):
      self.onto.save(file=self.output_filepath, format="rdfxml")
      print(f"Ontology saved to {self.output_filepath}")
   

test =  Reasoner("PizzaOntologyOWL.owl", "output_pizza.owl")
test.run_reasoner()
print("*******Reasoner finished********")
test.reason_subclasses()
print("*******Subclasses finished********")
test.save_ontology()
print("*******Ontology saved********")

      