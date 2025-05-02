# OntoPyLPG

This project provides a Python-based framework to map OWL ontologies to a labeled property graph (LPG) in Neo4j, infer new knowledge directly on the graph using a custom reasoner, and explore the ontology through a Streamlit-based frontend.

## Motivation

OWL ontologies are expressive but RDF-based triple stores can be limited when it comes to graph analytics. This project explores how OWL ontologies can be persisted and reasoned over in a graph database like Neo4j, leveraging its native Cypher querying and graph pattern matching.

## Project Structure

- `inputs/`  
  Folder where OWL ontology input files are placed for processing.

- `outputs/`  
  Folder to store outputs like inferred ontology files or exported graph data.

- `tests/`  
  Contains test scripts (e.g., pytest-based unit tests) to validate functionality of the project modules.

- `.env`  
  Stores environment variables like Neo4j credentials.

- `.gitignore`  
  Specifies intentionally untracked files to ignore in the Git repository.

- `README.md`  
  Project documentation and usage instructions.

- `requirements.txt`  
  List of Python package dependencies.

- `frontend.py`  
  Streamlit-based GUI for user interaction (upload, connect, query).

- `main.py`  
  CLI entry point for running the full processing pipeline.

---

### `ontopylpg/`

Main Python package containing all ontology-to-graph functionality.

- `Connector.py`  
  Manages the connection to the Neo4j database.

- `GraphMetaData.py`  
  Extracts and stores ontology-level metadata.

- `GraphReasoner.py`  
  Core reasoning logic for subclass, object property, inverse property, etc.

- `Mapper.py`  
  Converts OWL constructs into Neo4j property graph elements.

- `OWLHelper.py`  
  Helper functions for OWL term resolution and formatting.

- `OWLReadyReasoner.py`  
  Integrates Owlready2's built-in reasoner (if needed).

---

### ontopylpg/equivalent_reasoner/

Submodule for handling equivalence-specific reasoning.

- `EquivalenceReasoner.py`  
  Abstract class to implement equivalent reasoning functions.

- `EquivalenceReasoner1.py`  
  Concrete implementation of equivalence reasoning.

## Features

- Upload and parse OWL ontologies using Owlready2.
- Map OWL constructs to Neo4j's LPG model using py2neo.
- Perform custom reasoning directly on the Neo4j graph
- Interactive frontend using Streamlit.
- Modular and extensible codebase.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
