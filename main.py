from Connector import Connector
from py2neo import Node, Relationship
from GraphMetaData import GraphMetaData
from GraphReasoner import GraphReasoner
from OWLHelper import OWLHelper
from Mapper import Mapper

import os
from dotenv import load_dotenv

load_dotenv()

# filename = "inputs/PizzaOntology.rdf"
filename = "inputs/animal.owl"
format = "xml"
username = os.getenv("USERNAME_1")
password = os.getenv("PASSWORD")

#Estabilish connection
connection = Connector(username, password)
neo4j_graph = connection.connect_neo4j()

#Initial mapping
mapper = Mapper(neo4j_graph, filename, format)
mapper.map_all()

#Add metadata
onto_metadata = GraphMetaData(filename, neo4j_graph)
onto_metadata.add_all()

#Perform reasoning
graph_reasoner = GraphReasoner(neo4j_graph)
graph_reasoner.perform_reasoning()




# def main():
#     while True:
#         print("\nChoose an option:")
#         print("1. Map from OWL to LPG")
#         print("2. Perform reasoning")
#         print("3. Exit")

#         choice = input("Enter your choice: ")

#         if choice == "1":
#             filename = input("Enter the .owl filename: ")
#             Mapper_old.mapOWLtoLPG(filename)
            
#         elif choice == "2":
#             reasoning_save.reasoning_function(inferred_onto_path)
#             Mapper_old.mapOWLtoLPG(inferred_onto_path)
            
#         elif choice == "3":
#             print("Exiting program.")
#             break
        
#         else:
#             print("Invalid choice. Please try again.")

