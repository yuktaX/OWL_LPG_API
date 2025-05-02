import streamlit as st
from main import Main

# Streamlit App Configuration
st.set_page_config(layout="wide")
st.title("OntoPyLPG: A tool to persist, reason, and query on OWL files via Neo4j")

if 'main_instance' not in st.session_state:
    st.session_state.main_instance = Main(filename=None, username=None, password=None)

main_instance = st.session_state.main_instance

# Step 1: Enter Neo4j Username and Password
st.header("Step 1: Enter Neo4j Credentials")
username = st.text_input("Neo4j Username", value="", type="default")
password = st.text_input("Neo4j Password", value="", type="password")

if username and password:
      main_instance.username = username
      main_instance.password = password
      st.success("Credentials entered successfully!")

# Step 2: Connect to Neo4j
st.header("Step 2: Connect to Neo4j")
if st.button("Connect", type="secondary"):
   try:
      main_instance.establish_connection()
      st.success("Connected to Neo4j successfully!")
   except Exception as e:
      st.error(f"Failed to connect to Neo4j: {e}")
      
   print("--after conn", main_instance.neo4j_graph)
        
# Step 3: Upload OWL File
st.header("Step 3: Upload OWL File")
uploaded_file = st.file_uploader("Upload your .OWL or .RDF file", type=["owl", "rdf"])
if uploaded_file:
   # Determine the file extension
   file_extension = uploaded_file.name.split(".")[-1].lower()
   if file_extension in ["owl", "rdf"]:
      # Save the uploaded file locally
      file_path = f"inputs/uploaded_ontology.{file_extension}"
      with open(file_path, "wb") as f:
         f.write(uploaded_file.getbuffer())
      st.success(f"File uploaded successfully as {file_extension.upper()}!")
      main_instance.filename = file_path
   else:
      st.error("Invalid file type. Please upload a .OWL or .RDF file.")


# Step 4: Map the Ontology
st.header("Step 4: Map the Ontology")
if st.button("Map Ontology"):
   if main_instance:
      try:
         # print(main_instance.neo4j_graph)
         main_instance.clear_graph()
         main_instance.perform_initial_mapping()
         main_instance.add_metadata()
         st.success("Ontology mapped successfully!")
      except Exception as e:
         st.error(f"Error during mapping: {e}")
   else:
      st.error("Please upload an OWL file first.")
   
   
# Step 5: Perform Reasoning
st.header("Step 5: Perform Reasoning")
reasoner = st.selectbox("Select Reasoner", ["OntoPyLPG", "owlready"])
if st.button("Perform Reasoning"):
      if uploaded_file:
         try:
               main_instance.perform_reasoning(selected_reasoning=reasoner)
               st.success(f"Reasoning completed successfully using {reasoner}!")
         except Exception as e:
               st.error(f"Error during reasoning: {e}")
      else:
         st.error("Please upload an OWL file first.")

# Step 6: View Output in Neo4j Browser
st.header("Step 6: View Output")
neo4j_browser_link = "http://localhost:7474/browser/"
st.markdown(f"[View output in Neo4j Browser]({neo4j_browser_link})")