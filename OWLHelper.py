import rdflib
from owlready2 import *

class OWLHelper:
   def __init__(self, filename, format="xml"):
      self.filename = filename
      self.format = format
      
   def load_owl_rdf(self):
      rdf_graph = rdflib.Graph()
      rdf_graph.parse(self.filename, format=self.format)
      return rdf_graph

   def load_owl_ontology(self):
      onto = get_ontology(self.filename).load()
      return onto
   
   def extract_local_name(self, uri):
      uri = str(uri)
      if "#" in uri:
         return uri.split("#")[-1]
      elif "/" in uri:
         return uri.split("/")[-1]
      elif ":" in uri:
         return uri.split(":")[-1]
      else:
         return uri
      
   def rec_add_subclass(self, subcls, domain_classes):
      domain_classes.append(subcls)
      for cls in list(subcls.subclasses()):
         self.rec_add_subclass(cls, domain_classes)
         
   def rec_add_superclass(self, supercls, range_classes):
      range_classes.append(supercls)
      for cls in list(supercls.is_a):
         if isinstance(cls, ThingClass) and cls != supercls and not cls.name == 'Thing':
                        self.rec_add_superclass(cls, range_classes)