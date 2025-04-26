from py2neo import Graph, Node, Relationship

class GraphReasoner:
    def __init__(self, graph: Graph):
        self.graph = graph

    def add_inferred_subclass_relationships(self):
        # Fetch all class nodes
        class_nodes = self.graph.nodes.match("Class")
        
        for cls in class_nodes:
            self._process_subclasses(cls, cls)

    def _process_subclasses(self, ancestor_node, current_node):
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

            # Add inferred relationship: child --> ancestor
            # But only if child != ancestor (avoid self loops)
            if child_node.identity != ancestor_node.identity:
                inferred_rel = Relationship(child_node, "SUBCLASS_OF", ancestor_node)
                self.graph.merge(inferred_rel)

            # Recurse deeper: child becomes new current_node
            self._process_subclasses(ancestor_node, child_node)


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

            # 1. Add property to all subclasses and instances of a_node
            related_nodes = self._find_subclasses(a_node)+ self._find_individuals(a_node)
            print("----------------------------------------------------")
            print(a_node,rel_type,b_node)
            print(related_nodes)

            for related_node in related_nodes:
                new_rel = Relationship(related_node, rel_type, b_node)
                self.graph.merge(new_rel)

            # 2. Add property to all superclasses of b_node
            superclasses_b = self._find_superclasses(b_node)
            for super_b in superclasses_b:
                new_rel = Relationship(a_node, rel_type, super_b)
                self.graph.merge(new_rel)

    def _find_subclasses(self, node):
        # Find all subclasses and instances of a given class node
        query = """
        MATCH (sub:Class)-[:SUBCLASS_OF*0..]->(parent:Class)
        WHERE id(parent) = $node_id
        RETURN sub
        """

        result = self.graph.run(query, node_id=node.identity)
        if not result:
            return []
        return [record["sub"] for record in result]

    def _find_individuals(self,node):
        query = """
        MATCH (inst:Individual)-[:INSTANCE_OF]->(parent:Class)
        WHERE id(parent) = $node_id
        RETURN inst
        """
        result = self.graph.run(query, node_id=node.identity)
        if not result:
            return []
        return [record["inst"] for record in result]

    def _find_superclasses(self, node):
        # Find all superclasses of a given class node
        query = """
        MATCH (child:Class)-[:SUBCLASS_OF*1..]->(super:Class)
        WHERE id(child) = $node_id
        RETURN super
        """
        result = self.graph.run(query, node_id=node.identity)
        if not result:
            return []
        return [record["super"] for record in result]

graph = Graph("bolt://localhost:7687", auth=("neo4j", "neo4j_kt"))
reasoner = GraphReasoner(graph)
reasoner.add_inferred_subclass_relationships()
reasoner.add_inferred_object_properties()