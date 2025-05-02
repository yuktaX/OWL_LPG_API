from ontopylpg.Connector import Connector
from ontopylpg.GraphMetaData import GraphMetaData
from ontopylpg.GraphReasoner import GraphReasoner
from ontopylpg.Mapper import Mapper
from ontopylpg.OWLReadyReasoner import OWLReadyReasoner

import os
from dotenv import load_dotenv

load_dotenv()

class Main:
        
    def __init__(self, filename, username=None, password=None):
        self.filename = filename
        self.format = "xml"
        self.username = username
        self.password = password
        self.neo4j_graph = None
    
    def run(self, selected_reasoning):
        self.establish_connection()
        self.perform_initial_mapping()
        self.add_metadata()
        self.perform_reasoning(selected_reasoning)
        
        return self.neo4j_graph

    def establish_connection(self):
        if self.neo4j_graph is None:  # Only establish connection if not already connected
            connection = Connector(self.username, self.password)
            self.neo4j_graph = connection.connect_neo4j()
            if not self.neo4j_graph:
                raise Exception("Failed to connect to Neo4j.")
        return self.neo4j_graph

    def perform_initial_mapping(self):
        # print(main_instance.neo4j_graph)
        mapper = Mapper(self.neo4j_graph, self.filename, self.format)
        mapper.map_all()

    def add_metadata(self):
        onto_metadata = GraphMetaData(filename=self.filename, neo4j_graph=self.neo4j_graph)
        onto_metadata.add_all()

    def perform_reasoning(self, selected_reasoning):
        graph_reasoner = GraphReasoner(self.neo4j_graph)
        graph_reasoner.perform_reasoning()

        if selected_reasoning == "owlready":
            owlready_reasoner = OWLReadyReasoner(self.filename, "outputs/ontology.owl")
            owlready_reasoner = owlready_reasoner.run_owlready_reasoner()
            owlready_reasoner.save_ontology()
            mapper = Mapper(self.neo4j_graph, self.filename, self.format)
            mapper.map_all(filename="outputs/ontology.owl")
    
    def clear_graph(self):
        self.neo4j_graph.delete_all()

file = "inputs/PizzaOntology.rdf"
selected_reasoning = ""
main_instance = Main(file, username="neo4j", password="neo4j_kt")
main_instance.establish_connection()
print("---after conn", main_instance.neo4j_graph)

# main_instance.clear_graph()
main_instance.run(selected_reasoning = None)






