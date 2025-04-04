from owlready2 import *

def reasoning_function(inferred_onto_path):
    # Load ontology
    file_path = "file://example3.owl"
    onto = get_ontology(file_path).load()

    # Run reasoner
    with onto:
        sync_reasoner()

    # Add inferred subclass relationships to ontology explicitly
    for cls in onto.classes():
        for parent in cls.INDIRECT_is_a:
            if parent != cls:
                print(f"Inferred: {cls.name} is a subclass of {parent.name}")
                # Create subclass relation explicitly in ontology
                cls.is_a.append(parent)



    
    for indiv in onto.individuals():
        # Add inferred subclass relationships to individuals
        print("is_a")
        print(indiv.is_a)

        print(indiv.is_a[0].is_a)

        toAdd = set()
        for cls in indiv.is_a[0].is_a:
            if not(cls == indiv.is_a[0]):
                toAdd.add(cls)
                
        indiv.is_a.extend(toAdd)

        # Add inferred object properties explicitly # this is not working
        for prop in onto.object_properties():
            inferred_targets = getattr(indiv, prop.name, [])
            print("prop")
            print(prop.name)
            print("targets")
            print(inferred_targets)
            print("targets printed")
            for target in inferred_targets:
                if (indiv, prop, target) not in onto.world.sparql("""
                    SELECT ?s ?p ?o WHERE {
                        ?s ?p ?o .
                    }
                """):
                    print(f"Inferred: {indiv.name} {prop.name} {target.name}")
                    setattr(indiv, prop.name, [target])  # Explicitly add the relation
        print(indiv.is_a)

    # Save ontology with inferred facts



    onto.save(file=inferred_onto_path, format="rdfxml")

    print(f"Ontology with inferred relations saved as {inferred_onto_path}")

# print("calling function")
# reasoning_function()
# print("called function")
