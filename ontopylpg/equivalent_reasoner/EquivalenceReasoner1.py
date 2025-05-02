from ontopylpg.equivalent_reasoner.EquivalenceReasoner import EquivalenceReasoner

class EquivalenceReasoner1(EquivalenceReasoner):

        def evaluate_condition(self, class_node):
            class_name = class_node["name"]

            # Step 1: Get all required classes and relationship type
            query = """
            MATCH (class:CLASS_PROPERTY)-[:EQUIVALENT_TO]->(cond:EQUI_COND)-[r]->(c:CLASS_PROPERTY)
            WHERE id(class) = $class_id
            RETURN type(r) AS rel_type, collect(c.name) AS c_names
            """
            results = self.graph.run(query, class_id=class_node.identity).data()
            if not results:
                return

            for result in results:
                rel_type = result["rel_type"]
                required_classes = result["c_names"]

                print(f"rel_type = {rel_type}, required_classes = {required_classes}, class_name = {class_name}")

                ### ---------- INDIVIDUALS ----------
                individuals = self.graph.run("MATCH (i:Individual) RETURN i.name AS name").data()

                for ind in individuals:
                    ind_name = ind["name"]
                    print(f"Checking individual: {ind_name}")
                    all_classes_found = False

                    for cls in required_classes:
                        check_query = f"""
                        MATCH (i:Individual {{name: $ind_name}})
                        MATCH (i)-[:{rel_type.upper()}]->(tgt)
                        MATCH (tgt)-[:SUBCLASS_OF*0..]->(c:Class {{name: $cls}})
                        RETURN COUNT(*) > 0 AS exists
                        """
                        exists_result = self.graph.run(check_query, ind_name=ind_name, cls=cls).evaluate()

                        if exists_result:
                            all_classes_found = True
                            print(f"  ✗ Found one required cls: {cls}")
                            break

                    if all_classes_found:
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
                    all_classes_found = False

                    for cls in required_classes:
                        check_query = f"""
                        MATCH (cls:Class {{name: $cls_name}})
                        MATCH (cls)-[:{rel_type.upper()}]->(tgt)
                        MATCH (tgt)-[:SUBCLASS_OF*0..]->(c:Class {{name: $cls}})
                        RETURN COUNT(*) > 0 AS exists
                        """
                        exists_result = self.graph.run(check_query, cls_name=cls_name, cls=cls).evaluate()

                        if exists_result:
                            all_classes_found = True
                            print(f"  ✗ Found one required cls: {cls}")
                            break

                    if all_classes_found:
                        create_query = """
                        MATCH (sub:Class {name: $cls_name})
                        MATCH (super:Class {name: $class_name})
                        MERGE (sub)-[:SUBCLASS_OF]->(super)
                        """
                        self.graph.run(create_query, cls_name=cls_name, class_name=class_name)
                        print(f"  ✓ SUBCLASS_OF added: {cls_name} -> {class_name}")
