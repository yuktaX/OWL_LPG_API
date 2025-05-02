from py2neo import Graph, Node, Relationship, NodeMatcher
from ontopylpg.equivalent_reasoner.EquivalenceReasoner1 import EquivalenceReasoner1

class GraphReasoner:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.condition_handlers = {
            """
        MATCH (class:CLASS_PROPERTY)-[:EQUIVALENT_TO]->(cond:EQUI_COND)-[r]->(:CLASS_PROPERTY)
        RETURN DISTINCT class, type(r) AS rel_type, cond
        """: EquivalenceReasoner1(graph),
            # Add other handlers as needed
        }

        
    def add_inferred_subclass_relationships(self):
        class_nodes = self.graph.nodes.match("Class")
        
        for cls in class_nodes:
            self.process_subclasses(cls, cls)


    def process_subclasses(self, ancestor_node, current_node):
        # Recursively adds inferred SUBCLASS_OF relationships.
        # ancestor_node: The original ancestor class node.
        # current_node: The node we are currently exploring subclasses for.
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


    def find_subclasses(self, node):
        # Find all subclasses and instances of a given class node
        query = """
        MATCH (sub:Class)-[:SUBCLASS_OF*0..]->(parent:Class)
        WHERE id(parent) = $node_id
        RETURN sub as node
        """
        result = self.graph.run(query, node_id=node.identity)
        
        return [record["node"] for record in result]


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

            for record in result:
                inverse_node = record["b"]
                inverse_pairs[node["name"].upper()] = inverse_node["name"].upper()
        
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

        
    def infer_disjoint_closure(self):
        #Find indirect disjoint relationships and create direct ones.
        query = """
        MATCH (a:CLASS_PROPERTY)-[:DISJOINT]->(b:CLASS_PROPERTY)-[:DISJOINT]->(c:CLASS_PROPERTY)
        WHERE NOT (a)-[:DISJOINT]->(c)
        RETURN a, c
        """
        result = self.graph.run(query)

        for record in result:
            a = record["a"]
            c = record["c"]
            # Create inferred disjoint relationship
            disjoint_rel = Relationship(a, "DISJOINT", c)
            self.graph.merge(disjoint_rel)


    def mark_invalid_individuals(self):
        # Ensure the 'Nothing' class node exists
        self.graph.run("""
        MERGE (:Class {name: 'Nothing'})
        """)

        # Find individuals that are instances of disjoint classes
        query = """
        MATCH (i:Individual)-[:INSTANCE_OF]->(c1:Class),
            (i)-[:INSTANCE_OF]->(c2:Class),
            (cp1:CLASS_PROPERTY {name: c1.name}),
            (cp2:CLASS_PROPERTY {name: c2.name}),
            (cp1)-[:DISJOINT]->(cp2)
        //WHERE id(c1) < id(c2)  // avoid duplicates
        RETURN DISTINCT i.name AS ind_name
        """
        result = self.graph.run(query).data()

        for record in result:
            ind_name = record["ind_name"]

            # Delete all relationships of the individual
            delete_rels_query = """
            MATCH (i:Individual {name: $ind_name})-[r]-()
            DELETE r
            """
            self.graph.run(delete_rels_query, ind_name=ind_name)

            # Connect the individual to the 'Nothing' class
            subclass_query = """
            MATCH (i:Individual {name: $ind_name})
            MATCH (n:Class {name: 'Nothing'})
            MERGE (i)-[:SUBCLASS_OF]->(n)
            """
            self.graph.run(subclass_query, ind_name=ind_name)

            print(f"✗ Invalid individual: {ind_name} → reassigned under 'Nothing'")

    def process_disjoint_inference(self):
        #High-level function to run both steps.

        #adds transitively adds disjoint properties
        self.infer_disjoint_closure()

        #marks invlaid individuals as subclass or instance of the Nothing class
        self.mark_invalid_individuals()


    def add_inferred_transitive_relationships(self):
        # Fetch all ObjectProperties
        object_property_nodes = self.graph.nodes.match("ObjectProperty")
        transitive_properties = set()

        # Identify transitive object properties
        for node in object_property_nodes:
            query = """
            MATCH (a:ObjectProperty)-[:TRANSITIVE]->()
            WHERE id(a) = $node_id
            RETURN a
            """
            result = self.graph.run(query, node_id=node.identity)
            if result:
                transitive_properties.add(node["name"].upper())
        
        print("Found transitive properties:", transitive_properties)

        # For each transitive property, find all reachable nodes
        for prop in transitive_properties:
            query = f"""
            MATCH (start)-[:`{prop}`*2..]->(end)
            WHERE (start:Class OR start:Individual)
            AND (end:Class OR end:Individual)
            AND NOT (start)-[:`{prop}`]->(end)
            RETURN DISTINCT start, end
            """

            result = self.graph.run(query)

            for record in result:
                start_node = record["start"]
                end_node = record["end"]

                # Create the direct inferred relationship
                inferred_rel = Relationship(start_node, prop, end_node)
                self.graph.merge(inferred_rel)

                print(f"Created inferred transitive link: {start_node['name']} -[:{prop}]-> {end_node['name']}")
    

    def propagate_restrictions_to_subclasses(self):
        # Step 1: Get all class nodes with cardinality restriction properties
        query = """
        MATCH (parent:Class)
        WHERE any(key IN keys(parent) WHERE key STARTS WITH "has_cardinality_")
        RETURN parent
        """
        results = self.graph.run(query).data()

        for record in results:
            parent_node = record["parent"]
            parent_name = parent_node["name"]

            # Step 2: Find all subclasses (indirect too) of this parent node
            subclass_query = """
            MATCH (sub:Class)-[:SUBCLASS_OF*1..]->(parent:Class)
            WHERE id(parent) = $parent_id
            RETURN DISTINCT sub
            """
            subclasses = self.graph.run(subclass_query, parent_id=parent_node.identity).data()

            # Step 3: Get all keys from parent that are cardinality restrictions
            restriction_keys = [key for key in parent_node.keys() if key.startswith("has_cardinality_")]

            for subclass_record in subclasses:
                subclass_node = subclass_record["sub"]
                updated = False

                for key in restriction_keys:
                    # Only set if not already present
                    if key not in subclass_node:
                        subclass_node[key] = parent_node[key]
                        updated = True

                if updated:
                    self.graph.push(subclass_node)
                    print(f"Propagated restrictions from {parent_name} to subclass {subclass_node['name']}")
    def propagate_subproperty_relationships(self):
        # Step 1: Get all ObjectProperty nodes and their transitive ancestors via SUBPROPERTY_OF
        query_1 = """
        MATCH (child:ObjectProperty)-[:SUBPROPERTY_OF*1..]->(ancestor:ObjectProperty)
        RETURN child.name AS child_name, collect(DISTINCT ancestor.name) AS ancestors
        """
        result_1 = self.graph.run(query_1).data()

        for record in result_1:
            child_prop = record["child_name"]
            ancestor_props = record["ancestors"]

            print(f"\nProcessing property '{child_prop}' with ancestors {ancestor_props}")

            # Step 2: For each pair of class nodes connected by 'child_prop', add edges for all ancestors
            query_2 = f"""
            MATCH (a:Class)-[r:`{child_prop.upper()}`]->(b:Class)
            RETURN a, b
            """
            class_pairs = self.graph.run(query_2).data()

            for pair in class_pairs:
                a_node = pair["a"]
                b_node = pair["b"]


                for ancestor_prop in ancestor_props:
                    print(f"Adding inferred relationship: ({a_node['name']}) -[:{ancestor_prop.upper()}]-> ({b_node['name']})")

                    rel = Relationship(a_node, ancestor_prop.upper(), b_node)
                    self.graph.merge(rel)


    def apply_equivalence_reasoning(self):
        for query, handler in self.condition_handlers.items():
            results = self.graph.run(query)

            for record in results:
                class_node = record["class"]
                handler.evaluate_condition(class_node)

    def perform_reasoning(self):
        self.add_inferred_inverse_properties()
        self.add_inferred_subclass_relationships()
        self.process_disjoint_inference()
        self.apply_equivalence_reasoning()
        self.add_inferred_transitive_relationships()
        self.propagate_restrictions_to_subclasses()
        self.propagate_subproperty_relationships()
        
        print("Reasoning completed.")
    
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

            # Add property to all subclasses of a_node
            related_nodes = self.find_subclasses(a_node)

            for related_node in related_nodes:

                related_label = list(related_node.labels)[0]
                related_name = related_node["name"]

                b_label = list(b_node.labels)[0]
                b_name = b_node["name"]

                rel_type_dynamic = rel_type  # relationship type as a variable

                query = f"""
                MATCH (a:{related_label} {{name: $related_name}})
                MATCH (b:{b_label} {{name: $b_name}})
                MERGE (a)-[r:{rel_type_dynamic}]->(b)
                """
                self.graph.run(query, related_name=related_name, b_name=b_name)

            # Add property to all superclasses of b_node
            superclasses_b = self.find_superclasses(b_node)
            for super_b in superclasses_b:
                new_rel = Relationship(a_node, rel_type, super_b)
                self.graph.merge(new_rel)

    def propagate_properties_to_instances(self):
        # For each node 'a' that is an instance of class 'b', copy all of 'b''s outgoing relationships onto 'a'.
        # Find all (instance)-[:INSTANCE_OF]->(class) pairs
        instance_query = """
        MATCH (instance:Individual)-[:INSTANCE_OF]->(class:Class)
        RETURN instance, class
        """
        result = self.graph.run(instance_query)

        for record in result:
            instance_node = record["instance"]
            class_node = record["class"]

            # Find all outgoing edges from the class node (except SUBCLASS_OF and INSTANCE_OF)
            outgoing_edges_query = """
            MATCH (class:Class)-[r]->(target)
            WHERE id(class) = $class_id AND NOT type(r) IN ['SUBCLASS_OF', 'INSTANCE_OF']
            RETURN type(r) as rel_type, target
            """
            outgoing_edges = self.graph.run(outgoing_edges_query, class_id=class_node.identity)

            for edge_record in outgoing_edges:
                rel_type = edge_record["rel_type"]
                target_node = edge_record["target"]

                # Create the same relationship from instance_node to target_node
                new_rel = Relationship(instance_node, rel_type, target_node)
                self.graph.merge(new_rel)

                print(f"Created relationship: ({instance_node['name']})-[:{rel_type}]->({target_node['name']})")

