from py2neo import Graph, Node, Relationship

class GraphReasoner:
    def __init__(self, graph: Graph):
        self.graph = graph
    
    def perform_reasoning(self):
        # Add inferred subclass relationships
        self.add_inferred_subclass_relationships()
        # Add inferred object properties
        self.add_inferred_object_properties()
        # Add inferred inverse properties
        self.add_inferred_inverse_properties()
        
    def add_inferred_subclass_relationships(self):
        # Fetch all class nodes
        class_nodes = self.graph.nodes.match("Class")
        
        for cls in class_nodes:
            self.process_subclasses(cls, cls)

    def process_subclasses(self, ancestor_node, current_node):
        """
        Recursively adds inferred SUBCLASS_OF relationships.
        
        ancestor_node: The original ancestor class node.
        current_node: The node we are currently exploring subclasses for.
        """
        # Find direct subclasses of current_node
        query = """
        MATCH (child:Class)-[r]->(parent:Class)
        WHERE (type(r) = 'SUBCLASS_OF') AND id(parent) = $current_id
        RETURN child
        """
        result = self.graph.run(query, current_id=current_node.identity)

        for record in result:
            child_node = record["child"]

            # Add inferred relationship: child --> ancestor only if child != ancestor (avoid self loops)
            if child_node.identity != ancestor_node.identity:
                inferred_rel = Relationship(child_node, "SUBCLASS_OF", ancestor_node)
                self.graph.merge(inferred_rel)

            # Recurse deeper: child becomes new current_node
            self.process_subclasses(ancestor_node, child_node)


    def add_inferred_object_properties(self):
        # Find all object property relationships between Classes
        query = """
        MATCH (a:Class)-[r]->(b:Class)
        WHERE NOT type(r) = 'SUBCLASS_OF' AND NOT type(r) = 'INSTANCE_OF'
        RETURN a, type(r) as rel_type, b
        """
        result = self.graph.run(query)

        for record in result:
            a_node = record["a"]
            rel_type = record["rel_type"]
            b_node = record["b"]

            # Add property to all subclasses and instances of a_node
            related_nodes = self.find_subclasses(a_node)+ self.find_individuals(a_node)
            print("----------------------------------------------------")
            print(a_node,rel_type,b_node)
            print(related_nodes)

            for related_node in related_nodes:
                new_rel = Relationship(related_node, rel_type, b_node)
                self.graph.merge(new_rel)

            # Add property to all superclasses of b_node
            superclasses_b = self.find_superclasses(b_node)
            for super_b in superclasses_b:
                new_rel = Relationship(a_node, rel_type, super_b)
                self.graph.merge(new_rel)

    def find_subclasses(self, node):
        # Find all subclasses and instances of a given class node
        query = """
        MATCH (sub:Class)-[:SUBCLASS_OF*0..]->(parent:Class)
        WHERE id(parent) = $node_id
        RETURN sub
        """
        result = self.graph.run(query, node_id=node.identity)
        
        return [record["sub"] for record in result]

    def find_individuals(self,node):
        query = """
        MATCH (inst:Individual)-[:INSTANCE_OF]->(parent:Class)
        WHERE id(parent) = $node_id
        RETURN inst
        """
        result = self.graph.run(query, node_id=node.identity)
        
        return [record["inst"] for record in result]

    def find_superclasses(self, node):
        # Find all superclasses of a given class node
        query = """
        MATCH (child:Class)-[:SUBCLASS_OF*1..]->(super:Class)
        WHERE id(child) = $node_id
        RETURN super
        """
        result = self.graph.run(query, node_id=node.identity)
        
        return [record["super"] for record in result]

    def add_inferred_inverse_properties(self):
        # Fetch all object property nodes
        object_property_nodes = self.graph.nodes.match("ObjectProperty")
        inverse_pairs = {}
        
        for node in object_property_nodes:
            # Check if the node has an inverse property
            query = """
            MATCH (a:ObjectProperty)-[r:INVERSE_OF]->(b:ObjectProperty)
            WHERE id(a) = $node_id
            RETURN b
            """
            result = self.graph.run(query, node_id=node.identity)
            # print(result)

            for record in result:
                inverse_node = record["b"]
                inverse_pairs[node["name"].upper()] = inverse_node["name"].upper()
            
            print(inverse_pairs)
        
        for inverse_key, inverse_value in inverse_pairs.items():
            #Get all nodes with inverse_key as the edge
            query = """ 
            MATCH (a)-[r]->(b)
            WHERE type(r) = $inverse_key
            RETURN a, b """
            
            result = self.graph.run(query, inverse_key=inverse_key)
                        
            for record in result:
                a_node = record["a"]
                b_node = record["b"]
                
                # Create a relationship for the reverse edge
                inverse_relationship = Relationship(b_node, inverse_value.upper(), a_node)
                
                # Add the nodes and relationship to the graph
                self.graph.merge(inverse_relationship)

graph = Graph("bolt://localhost:7687", auth=("neo4j", "12345"))
reasoner = GraphReasoner(graph)
# reasoner.add_inferred_subclass_relationships()
# reasoner.add_inferred_object_properties()
reasoner.add_inferred_inverse_properties()