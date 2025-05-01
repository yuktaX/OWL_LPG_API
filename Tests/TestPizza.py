from main import Main

#cmd to run = PYTHONPATH=. pytest Tests/TestPizza.py 
#run from root dir

class TestPizzaOntology:
   @staticmethod
   def setup_method():
      filename = "inputs/PizzaOntology.rdf"
      main_instance = Main(filename)
      return main_instance.run(None)

   def test_transitive_instance(self):
      graph = self.setup_method()
      query = "MATCH (a)-[r:ISLIKE]->(b) WHERE a.name = 'AmericanaPizza1' AND b.name = 'SohoPizza1' RETURN a, r, b"
      result = list(graph.run(query))
      assert len(result) == 1, "Test 1 FAILED - TRANSITIVE"

   def test_transitive_instance_class(self):
      graph = self.setup_method()
      query = "MATCH (a)-[r:ISSPICIERTHAN]->(b) WHERE a.name = 'JalapenoPepperTopping' AND b.name = 'GreenPepperTopping' RETURN a, r, b"
      result = list(graph.run(query))
      assert len(result) == 1, "Test 1 FAILED - TRANSITIVE"

   def test_object_property(self):
      graph = self.setup_method()
      query = "MATCH (a)-[r:HASTOPPING]->(b) WHERE a.name = 'MargheritaPizza1' AND b.name = 'CheeseTopping' RETURN a, r, b"
      result = list(graph.run(query))
      assert len(result) == 1, "Test 2 FAILED - OBJECTPROPERTY"

   def test_subclass(self):
      graph = self.setup_method()
      query = "MATCH (a)-[r:SUBCLASS_OF]->(b) WHERE a.name = 'GreenPepperTopping' AND b.name = 'PizzaTopping' RETURN a, r, b"
      result = list(graph.run(query))
      assert len(result) == 1, "Test 3 FAILED - SUBCLASS"
   
   def test_inverse_1(self):
      graph = self.setup_method()
      query = "MATCH (a)-[r:ISTOPPINGOF]->(b) WHERE a.name = 'PizzaTopping' AND b.name = 'MargheritaPizza' RETURN a, r, b"
      result = list(graph.run(query))
      assert len(result) == 1, "Test 4 FAILED - INVERSE"
   
   def test_inverse_2(self):
      graph = self.setup_method()
      query = "MATCH (a)-[r:ISINGREDIENTOF]->(b) WHERE a.name = 'PizzaBase' AND b.name = 'SohoPizza' RETURN a, r, b"
      result = list(graph.run(query))
      assert len(result) == 1, "Test 5 FAILED - INVERSE"
