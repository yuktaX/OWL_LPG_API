from owlready2 import *

def reasoning_function(inferred_onto_path):
    # Load ontology
    file_path = "file://example3.owl"
    onto = get_ontology(file_path).load()
    print("FIRST CHECKK---BEFORE REASONING", set(onto.object_properties()))  

    # Run reasoner
    with onto:
        sync_reasoner()
    
    print("FIRST CHECKK---AFTER REASONING", set(onto.object_properties()))  

    # Add inferred subclass relationships to ontology explicitly
    for cls in onto.classes():
        for parent in cls.INDIRECT_is_a:
            if parent != cls:
                # print(f"Inferred: {cls.name} is a subclass of {parent.name}")
                # Create subclass relation explicitly in ontology
                cls.is_a.append(parent)
    
    # Add inferred subclass relationships to individuals
    for indiv in onto.individuals():
        
        inferred_relations = onto.world.sparql(f"""
        SELECT ?p WHERE {{
            <{indiv.iri}> ?p ?o .
        }}
    """)
        print("Inferred Properties:", list(inferred_relations))
        
        superclasses = indiv.is_a[0].is_a

        toAdd = set()
        for cls in superclasses:
            if cls != indiv.is_a[0]:
                toAdd.add(cls)
                
        indiv.is_a.extend(toAdd)
        # print(indiv, "----After adding superclasses---", indiv.is_a)
        print(f"Individual: {indiv.name}")
        print(f"  Class: {indiv.is_a}")
        print(f"  Properties: {list(indiv.get_properties())}")


        # Add inferred object properties explicitly 
        ## this is not working
        for prop in onto.object_properties():
            print("SECOND CHECKK---",prop.iri)
            # print("OPS---", indiv, prop.name, "properties--", indiv.get_properties())
            inferred_targets = getattr(indiv, prop.iri, [])
            print("prop - ", prop.name, " targets :", inferred_targets)
        
            for target in inferred_targets:
                if (indiv, prop, target) not in onto.world.sparql("""SELECT ?s ?p ?o WHERE {?s ?p ?o .}"""):
                    print(f"Inferred: {indiv.name} {prop.name} {target.name}")
                    setattr(indiv, prop.name, [target])  # Explicitly add the relation
        # print(indiv.is_a)

    # Save ontology with inferred facts
    onto.save(file=inferred_onto_path, format="rdfxml")

    print(f"Ontology with inferred relations saved as {inferred_onto_path}")

print("calling function")
reasoning_function("inferred_ontology_save_3.owl")
print("called function")
