import os
import io
import pandas as pd
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain_community.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
import streamlit as st
import warnings
warnings.filterwarnings("ignore")

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY"," my api key") 
APP_PASSWORD = os.getenv("APP_PASSWORD", "default")

if not OPENAI_API_KEY:
    raise ValueError("❌ Payment is pending for accessing this app...")

# Function to read CSV files
def read_csv_file(file_path):
    try:
        df = pd.read_csv(file_path)
        return df.to_string()
    except Exception as e:
        return f"Error reading CSV: {str(e)}"

# Tools for CSV file
csv_tool = Tool(
    name="Stillmeadow Inventory CSV Reader",
    func=lambda query: read_csv_file("stillmeadow_inventory.csv"),
    description="""
Reads data from the stillmeadow_inventory.csv file.

When the user asks about available items, or materials from a particular location, follow these rules:

1. If the query is general, return a clearly formatted bullet-point list in natural language, with:
   • Material Name -- Quantity -- Unit(if applicable), one material name per line.

2. If the user asks for materials relevant to **emergency situations** like:
   - Floods
   - Fire emergencies
   - Medical emergencies
   - Power outages
   - General disaster preparedness

...then intelligently analyze the inventory to find and list items that would be **useful or relevant in those contexts**. For example:
   • Cold pack for injuries
   • Flashlights or batteries for outages
   • Cleaning supplies for flood aftermath
   • First aid items for medical response

Only include **items that are actually listed in the inventory**. 
If the user asks for an explanation or usefulness, optionally add a 1-line explanation after each item. Return the results in bullet-point format as shown above.
"""

)

# Initialize LLM
llm = ChatOpenAI(temperature=0, model_name="gpt-4o", openai_api_key=OPENAI_API_KEY)

# Setup Conversation Memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Create LLM Agent with Multiple Tools
agent = initialize_agent(
    tools=[csv_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory,
    handle_parsing_errors=True,
    verbose=True
)

# Initialize Streamlit session state for history
if "history" not in st.session_state:
    st.session_state.history = []

# Sample queries list
sample_queries = [
    "What are the items available in Hallway?",
    "What are the materials available in shelf-1?",
    "How many Round tables are available with us?",
    "What are the items available on the Top Floor?",
    "Supplies available behind sandy hall curtain?",
    "Equipments available behind sandy hall curtain?",
    "Download full Stillmeadow inventory list"
]

# Streamlit Web Interface
def main():
    # col1, col2, col3 = st.columns([1,2,1])  # Creates three columns, middle one is wider
    # with col2:
    #     st.image("stillmeadow_logo.png", width=150)  # Add your logo in the center column

    # #st.write("Welcome to Stillmeadow Inventory Query System!")

    st.title("🏡 Stillmeadow Inventory Query System!")
    
    # Inject custom CSS for thick border
    st.markdown("""
    <style>
    div[data-baseweb="input"] > div {
        border: 3px solid #4CAF50 !important;  /* Thick green border */
        border-radius: 8px !important;
        padding: 6px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.form(key="query_form"):
        # Input for user query
        st.markdown("""
        <div style='font-size:24px; margin-bottom: -10px;'>
        Ask about the inventory:
        </div>
        """, unsafe_allow_html=True)
        user_query = st.text_input(label="", value=st.session_state.get('user_query', ''), placeholder="Type and press Enter/Submit Button...")
        submit = st.form_submit_button(label="Submit")

    #user_query = st.text_input("Ask about the inventory:", value=st.session_state.get('user_query', ''))
    #user_query = st.text_area("Ask about the inventory:", value=st.session_state.get('user_query', ''), height=100)
    
    # Ensure session variables exist
    if "last_executed_query" not in st.session_state:
        st.session_state.last_executed_query = ""
    if "last_response" not in st.session_state:
        st.session_state.last_response = ""
    if "history" not in st.session_state:
        st.session_state.history = []

# Handle query submission
    if (user_query or submit) and user_query.strip():
    # Only execute if this query is not the same as the last one
        if user_query != st.session_state.last_executed_query:
        # Run the query
            raw_response = agent.run(user_query)
            response = raw_response.replace("\\n", "\n")
            # Save response
            st.session_state.last_response = response
            # Save to history and update last executed
            st.session_state.history.append((user_query, response))
            st.session_state.last_executed_query = user_query
        else:
        # Use previous response if same query submitted again
            response = st.session_state.last_response
        # Display the response
        st.subheader("🤖 Stillmeadow's AI Response:")
        st.text(response)

        
    

    
    # Displaying the response based on the query
    # if user_query or submit:
    #     raw_response = agent.run(user_query)

    #     # Normalize line breaks (real, not HTML)
    #     response = raw_response.replace("\\n", "\n")

    #     # Main Response Display
    #     st.subheader("🤖 Stillmeadow's AI Response:")
    #     st.text(response)  # Use st.text to preserve newlines and bullets

    #     # Save clean version for history (no HTML)
    #     st.session_state.history.append((user_query, response))
    
        

        if "download" in user_query.lower() or "excel" in user_query.lower():
            try:
                df = pd.read_csv("stillmeadow_inventory.csv")
                response = "Click the button below to download the full inventory."

                # Create CSV in memory
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()

                st.download_button(
                    label="📥 Download Full Inventory items",
                    data=csv_data,
                    file_name="stillmeadow_inventory.csv"
                )
            except Exception as e:
                response = f"Error preparing file download: {str(e)}"

        # else:
        #     response = agent.run(user_query)

        # Add to history
        #st.session_state.history.append((user_query, response))
        
    # Display sample queries
    st.subheader("Sample Queries:")
    
    for query in sample_queries:
        if st.button(query, key=query):
            st.session_state.user_query = query  # Populate query into input field
            try:
                st.rerun()
            except AttributeError:
                st.experimental_rerun()
            
    # Display query history
    if st.session_state.history:
        st.subheader("**** Your Previous Queries ****")
        for idx, (query, answer) in enumerate(reversed(st.session_state.history), 1):
            st.write(f"**{idx}. Query:** {query}")
            st.write(f"**Response:** {answer}")
            st.write("---")

            
def check_password():
    def password_entered():
        if st.session_state["password"] == APP_PASSWORD:
            st.session_state["authenticated"] = True
            del st.session_state["password"]
        else:
            st.session_state["authenticated"] = False

    if "authenticated" not in st.session_state:
        st.text_input("🔐 Enter password to access the app:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["authenticated"]:
        st.text_input("🔐 Enter password to access the app:", type="password", on_change=password_entered, key="password")
        st.error("❌ Incorrect password. Try again.")
        return False
    else:
        return True

if __name__ == "__main__":
    if check_password():
        main()