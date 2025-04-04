from owlready2 import *

file_path = "file://example3.owl"

def extract_property_name(uri: str) -> str:
    """
    Extracts the property name from a given URI.
    
    Args:
        uri (str): The full URI of the property.
        
    Returns:
        str: The extracted property name.
    """
    if "#" in uri:
        return uri.split("#")[-1]  # Extract after #
    elif "/" in uri:
        return uri.rstrip("/").split("/")[-1]  # Extract last part after /
    return uri  # Return as-is if neither found

def reasoning_function(inferred_onto_path):
    # Load ontology
    
    onto = get_ontology(file_path).load()

    # Run reasoner
    with onto:
        sync_reasoner()
    
    # Add inferred subclass relationships to ontology explicitly
    for cls in onto.classes():
        for parent in cls.INDIRECT_is_a:
            if parent != cls:
                # print(f"Inferred: {cls.name} is a subclass of {parent.name}")
                # Create subclass relation explicitly in ontology
                cls.is_a.append(parent)
    
    # result_set_a = list(onto.world.sparql("""SELECT ?s ?p ?o WHERE {?s ?p ?o .}"""))
    # print("-----------",(result_set_a, len(result_set_a)), "-----------------")


    for indiv in onto.individuals():
        
        #when new ancestor nodes are created, the triple is automatically added into onto.world
        superclasses = indiv.is_a[0].is_a

        toAdd = set()
        for cls in superclasses:
            if cls != indiv.is_a[0]:
                toAdd.add(cls)
                
        indiv.is_a.extend(toAdd)
        
        print(f"Individual: {indiv.name}")
        print(f"Class: {indiv.is_a}")
        print(f"Explicit Properties: {list(indiv.get_properties())}")
        
        inferred_properties = list(onto.world.sparql(f"""SELECT ?p WHERE {{<{indiv.iri}> ?p ?o .}}"""))
        
        current_properties = []
        
        for property in inferred_properties:
            if type(property[0]) is str:
                for item in property:
                    current_properties.append(item)
        
        current_targets = []
            
        for relation in current_properties:
            inferred_targets = list(onto.world.sparql(f"""SELECT ?o WHERE {{<{indiv.iri}> <{relation}> ?o .}}"""))
            for item in inferred_targets[0]:                
                current_targets.append(item)
        
        # print(current_properties, current_object_properties)
        result_set = list(onto.world.sparql("""SELECT ?s ?p ?o WHERE {?s ?p ?o .}"""))
        
        for prop in current_properties:
            # prop = extract_property_name(prop_uri)
            for target in current_targets:
                triplet = [indiv, prop, target]
                if triplet not in result_set:
                    print("----NEW TRIPLE----", triplet)
                    setattr(indiv, prop, target)
                    
        result_set_after = list(onto.world.sparql("""SELECT ?s ?p ?o WHERE {?s ?p ?o .}"""))
        print(len(result_set_after))

    onto.save(file=inferred_onto_path, format="rdfxml")
    print(f"Ontology with inferred relations saved as {inferred_onto_path}")

reasoning_function("inferred_ontology_save_3.owl")
print("called function")
