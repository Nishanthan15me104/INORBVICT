import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# --- Dynamically add project root to Python path ---
# Since this file is in 'chatbotapi/', the project root is the parent directory.
# This ensures that imports like 'from chatbotapi.src...' can be resolved.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
# --------------------------------------------------------------------------------

# Import the necessary components using the full project path
# FIX: CHANGED TO A RELATIVE IMPORT from the 'application' level 
#       to resolve the persistent ModuleNotFoundError.
# We assume test_rag_service.py is in 'chatbotapi/' and needs to reach
# 'src/chat/application/convo/rag_query_service.py'
from src.chat.application.convo.response_generation import HybridGenerator

# Load environment variables
load_dotenv()

def main():
    """Initializes the Hybrid Generator and runs two test queries."""
    
    # Check for API Key
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("FATAL ERROR: GROQ_API_KEY environment variable not found.")
        print("Please set GROQ_API_KEY in your .env file or system environment.")
        sys.exit(1)

    # 1. Initialize the Service
    try:
        generator = HybridGenerator(groq_api_key=groq_api_key)
        print("\n--- Hybrid Generator Initialized (FAISS Loaded) ---\n")
    except Exception as e:
        print(f"Error initializing generator: {e}")
        print("Make sure you installed 'sentence-transformers' and your FAISS index is present.")
        sys.exit(1)
        
    # 2. Test RAG Query (Should hit the index)
    query_rag = "What is Jordan Peterson's position on the importance of order and chaos?"
    print(f"QUERY 1 (RAG Expected): {query_rag}")
    response_rag = generator(query_rag)
    print("--------------------------------------------------")
    print(f"RESPONSE 1:\n{response_rag['response']}")
    print("--------------------------------------------------\n")
    
    # 3. Test LLM Query (Should bypass the index)
    query_llm = "What is the capital of France?"
    print(f"QUERY 2 (LLM Expected): {query_llm}")
    response_llm = generator(query_llm)
    print("--------------------------------------------------")
    print(f"RESPONSE 2:\n{response_llm['response']}")
    print("--------------------------------------------------")
    

if __name__ == "__main__":
    main()
