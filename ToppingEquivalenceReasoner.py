from EquivalenceReasoner import EquivalenceReasoner

class ToppingEquivalenceReasoner(EquivalenceReasoner):
    def evaluate_condition(self, class_node):
        class_name = class_node["name"]
        
        # 1. Get all required toppings for this class from metadata
        query = """
        MATCH (class:CLASS_PROPERTY)-[:EQUIVALENT_TO]-(cond:EQUI_COND)-[r]->(topping:CLASS_PROPERTY)
        WHERE id(class) = $class_id
        RETURN type(r) AS rel_type, collect(topping.name) AS topping_names
        """
        result = self.graph.run(query, class_id=class_node.identity).evaluate()
        
        if not result:
            return  # No condition metadata

        rel_type, required_toppings = result["rel_type"], result["topping_names"]

        # 2. Find individuals that are connected to ALL required toppings via rel_type (e.g., hasTopping)
        infer_query = f"""
        MATCH (i:Individual)
        WHERE ALL(t IN $required_toppings WHERE 
            (i)-[:{rel_type}]->(:Class {{name: t}})
        )
        MERGE (i)-[:INSTANCE_OF]->(:Class {{name: $class_name}})
        """
        self.graph.run(infer_query, required_toppings=required_toppings, class_name=class_name)
