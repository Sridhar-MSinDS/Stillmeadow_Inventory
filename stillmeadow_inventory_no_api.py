# -*- coding: utf-8 -*-
"""stillmeadow_inventory.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1CmBGF1xoOTzN-LhO6hisBZfb76IE05bW
"""

import os
import pandas as pd
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain_community.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor
import streamlit as st

# 1️⃣ Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY","your_api_key")
#OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

if not OPENAI_API_KEY:
    raise ValueError("❌ OpenAI API Key is missing! Set the OPENAI_API_KEY environment variable.")

# Function to read CSV files
def read_csv_file(file_path):
    try:
        df = pd.read_csv(file_path)
        return df.to_string()
    except Exception as e:
        return f"Error reading CSV: {str(e)}"

# Tools for CSV files
csv_tool = Tool(
    name="Stillmeadow Inventory CSV Reader",
    func=lambda query: read_csv_file("stillmeadow_inventory.csv"),
    description="Reads inventory data from the stillmeadow_inventory.csv file."
)


# Initialize LLM
llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY)

# Setup Conversation Memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Create LLM Agent with Multiple Tools
agent = initialize_agent(
    tools=[csv_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)

agent_executor = AgentExecutor(agent = agent, tools = [csv_tool], verbose=True, handle_parsing_errors=True)

# Initialize Streamlit session state for history
if "history" not in st.session_state:
    st.session_state.history = []

# Sample queries list
sample_queries = [
    "What are the items available in Rack-1?",
    "What are the items available in Rack-2?",
    "What are the items available in Rack-3?",
    "What are the items available in Rack-4?",
    "What are the items available in hallway?",
    "What are the items available in Top Floor?",
    "What are the items available in Basement?"
]

# Streamlit Web Interface
def main():
    col1, col2, col3 = st.columns([1,2,1])  # Creates three columns, middle one is wider
    with col2:
        st.image("stillmeadow_logo.png", width=150)  # Add your logo in the center column

    #st.write("Welcome to Stillmeadow Inventory Query System!")

    st.title("Stillmeadow Inventory Query System!")

    # Display sample queries
    st.subheader("Sample Queries:")
    for query in sample_queries:
        if st.button(query, key=query):
            st.session_state.user_query = query  # Populate query into input field
            try:
                st.rerun()
            except AttributeError:
                st.experimental_rerun()


    # Input for user query
    user_query = st.text_input("Ask about the inventory:", value=st.session_state.get('user_query', ''))
   # Initialize response variable (empty or None initially)
    response = None  

    # Displaying the response based on the query
    if user_query:
        try:
            response = agent_executor.run(user_query)
            
            st.write(response)  # Display the response
            
            
        except Exception as e:
            st.write(f"Error processing the query: {e}")
    else:
        st.write("Please enter a query.")

    # Add to history only if a valid response exists
    if user_query and response:
        st.session_state.history.append((user_query, response))

    

    # Display query history
    if st.session_state.history:
        st.subheader("Your Previous Queries:")
        for idx, (query, answer) in enumerate(reversed(st.session_state.history), 1):
            st.write(f"**{idx}.** Query: {query}")
            st.write(f"**Response:** {answer}")
            st.write("---")

if __name__ == "__main__":
    main()
