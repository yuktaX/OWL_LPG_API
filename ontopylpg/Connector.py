from py2neo import Graph as NeoGraph

class Connector:
   
   def __init__(self, username, password):
      self.username = username
      self.password = password
      self.format = format
      self.neo4j_graph = None
      
   def connect_neo4j(self):
      try:
         self.neo4j_graph = NeoGraph("bolt://localhost:7687", auth=(self.username, self.password))
         self.neo4j_graph.delete_all()
         return self.neo4j_graph
      except Exception as e:
         print(f"Failed to connect to Neo4j: {e}")
         self.neo4j_graph = None
         return None
   
   def close_connection(self):
      if self.neo4j_graph:
         self.neo4j_graph = None
         print("Neo4j connection closed.")
      else:
         print("No active Neo4j connection to close.")
         
   def execute_query(self, query):
      if not self.neo4j_graph:
         raise ConnectionError("Not connected to Neo4j. Call connect_neo4j() first.")
      return self.neo4j_graph.run(query).data()
