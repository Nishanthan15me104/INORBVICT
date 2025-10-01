import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

# 1. Load the .env file
# This loads the GROQ_API_KEY into your environment variables
load_dotenv()

# --- Setup LangChain Groq Model ---

# The ChatGroq class automatically finds the GROQ_API_KEY 
# from the environment variables loaded by load_dotenv()
# 🚀 Specify the model (e.g., Mixtral-8x7b-Instruct-v0.1)
llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)

# --- Define the Prompt and Chain ---

# 2. Define the message/prompt
user_query = "Explain the speed of Groq."

# A simple prompt template is a good practice
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a concise and helpful AI assistant."),
    ("human", "{text}")
])

# Create the chain: Prompt -> Model
chain = prompt | llm

# --- Invoke the Chain and Print the Result ---

# 3. Invoke the chain
response = chain.invoke({"text": user_query})

# 4. Print the response
print("--- Groq Response ---")
print(response.content)

# Alternatively, you can use the simpler .invoke() directly on the model:
# response_direct = llm.invoke([HumanMessage(content=user_query)])
# print(response_direct.content)