from ontopylpg.equivalent_reasoner.EquivalenceReasoner import EquivalenceReasoner

class EquivalenceReasoner1(EquivalenceReasoner):
            
        def evaluate_condition(self, class_node):
            class_name = class_node["name"]

            # Step 1: Get all required toppings and relationship type
            query = """
            MATCH (class:CLASS_PROPERTY)-[:EQUIVALENT_TO]->(cond:EQUI_COND)-[r]->(topping:CLASS_PROPERTY)
            WHERE id(class) = $class_id
            RETURN type(r) AS rel_type, collect(topping.name) AS topping_names
            """
            results = self.graph.run(query, class_id=class_node.identity).data()
            if not results:
                return

            for result in results:
                rel_type = result["rel_type"]
                required_toppings = result["topping_names"]

                print(f"rel_type = {rel_type}, required_toppings = {required_toppings}, class_name = {class_name}")

                ### ---------- INDIVIDUALS ----------
                individuals = self.graph.run("MATCH (i:Individual) RETURN i.name AS name").data()

                for ind in individuals:
                    ind_name = ind["name"]
                    print(f"Checking individual: {ind_name}")
                    all_toppings_found = True

                    for topping in required_toppings:
                        check_query = f"""
                        MATCH (i:Individual {{name: $ind_name}})
                        MATCH (i)-[:{rel_type.upper()}]->(tgt)
                        MATCH (tgt)-[:SUBCLASS_OF*0..]->(c:Class {{name: $topping}})
                        RETURN COUNT(*) > 0 AS exists
                        """
                        exists_result = self.graph.run(check_query, ind_name=ind_name, topping=topping).evaluate()

                        if not exists_result:
                            all_toppings_found = False
                            print(f"  ✗ Missing required topping: {topping}")
                            break

                    if all_toppings_found:
                        create_query = """
                        MATCH (i:Individual {name: $ind_name})
                        MATCH (c:Class {name: $class_name})
                        MERGE (i)-[:INSTANCE_OF]->(c)
                        """
                        self.graph.run(create_query, ind_name=ind_name, class_name=class_name)
                        print(f"  ✓ INSTANCE_OF added: {ind_name} -> {class_name}")

                ### ---------- CLASSES ----------
                classes = self.graph.run("MATCH (c:Class) RETURN c.name AS name").data()

                for cls in classes:
                    cls_name = cls["name"]
                    if cls_name == class_name:
                        continue  # Skip self
                    print(f"Checking class: {cls_name}")
                    all_toppings_found = True

                    for topping in required_toppings:
                        check_query = f"""
                        MATCH (cls:Class {{name: $cls_name}})
                        MATCH (cls)-[:{rel_type.upper()}]->(tgt)
                        MATCH (tgt)-[:SUBCLASS_OF*0..]->(c:Class {{name: $topping}})
                        RETURN COUNT(*) > 0 AS exists
                        """
                        exists_result = self.graph.run(check_query, cls_name=cls_name, topping=topping).evaluate()

                        if not exists_result:
                            all_toppings_found = False
                            print(f"  ✗ Class missing topping: {topping}")
                            break

                    if all_toppings_found:
                        create_query = """
                        MATCH (sub:Class {name: $cls_name})
                        MATCH (super:Class {name: $class_name})
                        MERGE (sub)-[:SUBCLASS_OF]->(super)
                        """
                        self.graph.run(create_query, cls_name=cls_name, class_name=class_name)
                        print(f"  ✓ SUBCLASS_OF added: {cls_name} -> {class_name}")




    # def evaluate_condition(self, class_node):
    #     class_name = class_node["name"]
        
    #     # 1. Get all required toppings for this class from metadata
    #     query = """
    #     MATCH (class:CLASS_PROPERTY)-[:EQUIVALENT_TO]->(cond:EQUI_COND)-[r]->(topping:CLASS_PROPERTY)
    #     WHERE id(class) = $class_id
    #     RETURN type(r) AS rel_type, collect(topping.name) AS topping_names
    #     """
    #     # result = self.graph.run(query, class_id=class_node.identity).evaluate()
    #     results = self.graph.run(query, class_id=class_node.identity).data()
        
    #     if not results:
    #         return  # No condition metadata

    #     for result in results:
    #         rel_type, required_toppings = result["rel_type"], result["topping_names"]
    #         print("rel_type = ",rel_type," required_toppings = ",required_toppings," class_name = ",class_name)

    #         # 2. Find individuals that are connected to ALL required toppings via rel_type (e.g., hasTopping)
    #         # infer_query = f"""
    #         # MATCH (i:Individual)
    #         # WHERE ALL(t IN $required_toppings WHERE 
    #         #     (i)-[:{rel_type.upper()}]->(:Class {{name: t}})
    #         # )
    #         # MERGE (i)-[:INSTANCE_OF]->(:Class {{name: $class_name}})
    #         # """

    #         # instance_query = """
    #         # MATCH (instance:Individual)-[:INSTANCE_OF]->(class:Class)
    #         # RETURN instance, class
    #         # """

    #         infer_query = """
    #         MATCH (c:Class {{name: $class_name}})
    #         MATCH (i:Individual)
    #         WHERE EXISTS{{MATCH ((i)-[:{rel_type.upper()}]->(tgt))
    #                 MATCH ((tgt)-[:SUBCLASS_OF*0..]->(c:Class {{name:t}}))
    #                 RETURN tgt, c}}
    #         RETURN i
    #         """

    #         # results = self.graph.run(instance_query)
    #         # for result in results:
    #         #     infer_res = self.graph.run(infer_query)
    #         #     if infer_query:
                
                




            # infer_query = f"""
            # MATCH (c:Class {{name: $class_name}})
            # MATCH (i:Individual)
            # WHERE ALL(t IN $required_toppings WHERE 
            #     (i)-[:{rel_type.upper()}]->(:Class {{name: t}})
            # )
            # MERGE (i)-[:INSTANCE_OF]->(c)
            # """

            # infer_query = f"""
            # MATCH (c:Class {{name: $class_name}})
            # MATCH (i:Individual)
            # WHERE ALL(t IN $required_toppings WHERE 
            #     EXISTS {{
            #         MATCH ((i)-[:{rel_type.upper()}]->(tgt))
            #         MATCH ((tgt)-[:SUBCLASS_OF*0..]->(c:Class {{name:t}}))
            #         RETURN tgt, c
            #     }}
            # )
            # MERGE (i)-[:INSTANCE_OF]->(c)
            # """

            # infer_query = f"""
            # MATCH (c:Class {{name: $class_name}})
            # MATCH (i:Individual)
            # WHERE ALL(t IN $required_toppings WHERE 
            #     EXISTS {{
            #         MATCH (i)-[:{rel_type.upper()}]->(tgt)
            #         MATCH (tgt)-[:SUBCLASS_OF*0..]->(super:Class)
            #         WHERE super.name = t
            #         RETURN super
            #     }}
            # )
            # MERGE (i)-[:INSTANCE_OF]->(c)
            # """



            # self.graph.run(infer_query, required_toppings=required_toppings, class_name=class_name)
