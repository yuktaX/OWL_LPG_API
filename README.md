# OntoPyLPG

This project provides a Python-based framework to map OWL ontologies to a labeled property graph (LPG) in Neo4j, infer new knowledge directly on the graph using a custom reasoner, and explore the ontology through a Streamlit-based frontend.

## 🧠 Motivation

OWL ontologies are expressive but RDF-based triple stores can be limited when it comes to graph analytics. This project explores how OWL ontologies can be persisted and reasoned over in a graph database like Neo4j, leveraging its native Cypher querying and graph pattern matching.

## 📁 Project Structure

- `inputs/`  
  Directory for `.owl` files to be uploaded and processed.

- `outputs/`  
  Stores generated or exported artifacts like RDF/XML outputs or logs.

- `frontend.py`  
  Streamlit app to upload OWL files, trigger reasoning, and visualize results.

- `main.py`  
  Entrypoint script that ties together mapping, reasoning, and Neo4j connection.

- `Connector.py`  
  Handles connection setup and authentication to the Neo4j database.

- `Mapper.py`  
  Maps OWL entities (classes, individuals, properties) into the Neo4j property graph.

- `GraphMetaData.py`  
  Handles ontology-level metadata like ontology IRI, namespaces, and base URI.

- `OWLHelper.py`  
  Utility functions for OWL file parsing and ontology manipulation using Owlready2.

- `OWLReadyReasoner.py`  
  Adds inferred subclass and property relationships using Owlready2's reasoner.

- `GraphReasoner.py`  
  Custom reasoner that performs graph-based inferencing directly in Neo4j using Cypher.

- `EquivalenceReasoner1.py`  
  (Optional) Handles `owl:sameAs` or equivalence-related reasoning tasks.

- `Tests/`  
  Contains unit and integration tests (pytest-based).

- `.env`  
  Environment variables for sensitive info like Neo4j credentials.

- `requirements.txt`  
  Python package dependencies.

## 🚀 Features

- Upload and parse OWL ontologies using Owlready2.
- Map OWL constructs to Neo4j's LPG model using py2neo.
- Perform custom reasoning directly on the Neo4j graph
- Interactive frontend using Streamlit.
- Modular and extensible codebase.

## 🛠️ Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
