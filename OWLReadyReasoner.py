from owlready2 import *
import rdflib
from rdflib.namespace import RDF, RDFS, OWL

class OWLReadyReasoner:
   
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
         
   def run_owlready_reasoner(self):
      with self.onto:
         sync_reasoner()
   
   def save_ontology(self):
      self.onto.save(file=self.output_filepath, format="rdfxml")
      print(f"Ontology saved to {self.output_filepath}")
   

# test =  Reasoner("example3.owl", "output_alice.owl")
# test = Reasoner("inputs/animal.owl","outputs/animal.owl")
# test.run_owlready_reasoner()
# print("*******Reasoner finished********")
# test.save_ontology()
# print("*******Ontology saved********")