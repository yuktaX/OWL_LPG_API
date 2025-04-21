import reasoning_save
import Mapper

inferred_onto_path = "inferred_ontology_save_3.owl"

def main():
    while True:
        print("\nChoose an option:")
        print("1. Map from OWL to LPG")
        print("2. Perform reasoning")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            filename = input("Enter the .owl filename: ")
            Mapper.mapOWLtoLPG(filename)
            
        elif choice == "2":
            reasoning_save.reasoning_function(inferred_onto_path)
            Mapper.mapOWLtoLPG(inferred_onto_path)
            
        elif choice == "3":
            print("Exiting program.")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
