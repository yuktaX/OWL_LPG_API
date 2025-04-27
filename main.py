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
# filename = "inputs/animal.owl"

class Main:
    
    def __init__(self, filename):
        self.filename = filename
        self.format = "xml"
        self.username = os.getenv("USERNAME_1")
        self.password = os.getenv("PASSWORD")
        
    def run(self):
        #Establish connection
        connection = Connector(self.username, self.password)
        neo4j_graph = connection.connect_neo4j()

        #Initial mapping
        mapper = Mapper(neo4j_graph, self.filename, self.format)
        mapper.map_all()

        #Add metadata
        onto_metadata = GraphMetaData(self.filename, neo4j_graph)
        onto_metadata.add_all()

        #Perform reasoning
        graph_reasoner = GraphReasoner(neo4j_graph)
        graph_reasoner.perform_reasoning()
        
        return neo4j_graph


main_instance = Main("inputs/PizzaOntology.rdf")
main_instance.run()





