from Connector import Connector
from py2neo import Node, Relationship
from GraphMetaData import GraphMetaData
from GraphReasoner import GraphReasoner
from OWLHelper import OWLHelper
from Mapper import Mapper
from OWLReadyReasoner import OWLReadyReasoner

import os
from dotenv import load_dotenv

load_dotenv()

class Main:
    
    def __init__(self, filename):
        self.filename = filename
        self.format = "xml"
        self.username = os.getenv("USERNAME_1")
        self.password = os.getenv("PASSWORD")
        
    def run(self, selected_reasoning):
        #Establish connection
        connection = Connector(self.username, self.password)
        neo4j_graph = connection.connect_neo4j()

        #Initial mapping
        mapper = Mapper(neo4j_graph, self.filename, self.format)
        mapper.map_all()

        #Add metadata
        onto_metadata = GraphMetaData(self.filename, neo4j_graph)
        onto_metadata.add_all()

        #Perform custom reasoning
        graph_reasoner = GraphReasoner(neo4j_graph)
        graph_reasoner.perform_reasoning()
        
        if selected_reasoning == "owlready":
            owlready_reasoner = OWLReadyReasoner(self.filename, "outputs/ontology.owl")
            owlready_reasoner = owlready_reasoner.run_owlready_reasoner()
            owlready_reasoner.save_ontology()
            mapper.map_all(filename="outputs/ontology.owl")
        
        return neo4j_graph

file = "inputs/PizzaOntology.rdf"
selected_reasoning = "owlready"
main_instance = Main(file)
main_instance.run(selected_reasoning = None)





