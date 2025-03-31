# OWL_LPG_API

## 1. Mapping OWL to LPG format

| **OWL Element**                              | **LPG Representation (Neo4j)**                               |
| -------------------------------------------- | ------------------------------------------------------------ |
| **Class (`owl:Class`)**                      | Node labeled as the class name (`:Person`, `:City`)          |
| **Individual (`owl:NamedIndividual`)**       | Node with label from its class (`(:Person {name: "Alice"})`) |
| **Object Property (`owl:ObjectProperty`)**   | Relationship type (`(:Person)-[:livesIn]->(:City)`)          |
| **Data Property (`owl:DatatypeProperty`)**   | Node property (`(:Person {age: 25})`)                        |
| **SubClass (`rdfs:subClassOf`)**             | `(:ClassA)-[:SUBCLASS_OF]->(:ClassB)`                        |
| **Equivalent Class (`owl:equivalentClass`)** | `(:ClassA)-[:EQUIVALENT_TO]->(:ClassB)`                      |
| **Same Individual (`owl:sameAs`)**           | `(:EntityA)-[:SAME_AS]->(:EntityB)`                          |

### Key Features

1. **Fully LPG-Compatible**
   - No RDF metadata retained; everything is structured for **efficient Cypher queries**.
2. **Query Optimization**
   - Direct Cypher queries like `MATCH (p:Person)-[:livesIn]->(c:City)` instead of complex RDF-based queries.
3. **Data Property Storage**

   - Attributes like `age`, `name` are stored as **node properties** instead of separate nodes.

4. **Ontology-Based Structuring**
   - Subclass and equivalence relations are explicitly represented for **better reasoning support**.
