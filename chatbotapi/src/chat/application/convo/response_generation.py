import os
import sys
from pathlib import Path
from typing import Dict, Any

from loguru import logger
from groq import Groq

# Ensure project root is in path for imports to work
# FIX 1: Corrected depth from parents[4] to parents[5] to reach the project root 
# (C:\Documents\assign_chatbot) from this file's location.
PROJECT_ROOT = Path(__file__).resolve().parents[5] 
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Simplified imports now that sys.path is fixed
from chatbotapi.src.chat.application.rag.retrievers import get_retriever 
from langchain_core.runnables import RunnablePassthrough, RunnableBranch
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

# --- Hardcoded RAG Configuration (Matching setup_rag.py) ---
RAG_EMBEDDING_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
RAG_CHUNK_SIZE = 256
GROQ_LLM_MODEL = "llama-3.1-8b-instant"
GROQ_RAG_MODEL = "llama-3.1-8b-instant"
FAISS_INDEX_PATH = "faiss_index"
RAG_TOP_K = 3
# ----------------------------------------------------------

class HybridGenerator:
    """
    A service that determines if a query is related to Jordan Peterson (JP) 
    and chooses between a RAG approach (using the FAISS index) or a direct
    LLM query (for general knowledge).
    """
    def __init__(self, groq_api_key: str):
        """Initializes the Groq client and the RAG/LLM chains."""
        
        # 1. Initialize Groq Clients
        # Note: ChatGroq requires GROQ_API_KEY environment variable to be set.
        self.llm_classifier = ChatGroq(temperature=0.0, model_name=GROQ_LLM_MODEL, groq_api_key=groq_api_key)
        self.llm_generator = ChatGroq(temperature=0.1, model_name=GROQ_RAG_MODEL, groq_api_key=groq_api_key)
        
        # 2. Load the Retriever (Loads the FAISS index from disk)
        # FIX: Calling get_retriever with the exact arguments required by its signature:
        # embedding_model_id, k, and device.
        # Arguments 'top_k' and 'faiss_index_path' are explicitly omitted as they caused errors.
        self.retriever = get_retriever(
            embedding_model_id=RAG_EMBEDDING_MODEL_ID, 
            device="cpu", 
            k=RAG_TOP_K, 
        )
        logger.info("FAISS index loaded successfully.")
        
        # 3. Build the Hybrid Chain
        self.chain = self._build_hybrid_chain()
        
    def _build_hybrid_chain(self):
        """Constructs the RunnableBranch for intent-based routing."""
        
        # --- 3.1 Intent Classification Prompt ---
        classifier_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an intent router. Your task is to classify the user query. "
                         "If the query is primarily about 'Jordan Peterson', respond with 'RAG'. "
                         "Otherwise, respond with 'LLM'. Only output the classification word, nothing else."),
            ("human", "{query}")
        ])
        
        # Intent chain: Query -> Prompt -> LLM -> Output
        intent_chain = classifier_prompt | self.llm_classifier
        
        # --- 3.2 RAG Chain (for Jordan Peterson queries) ---
        rag_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a specialized assistant on Jordan Peterson. "
                         "Answer the user's question ONLY using the following context. "
                         "If the context does not contain the answer, state that you cannot answer based on the provided documents.\n\n"
                         "Context: {context}"),
            ("human", "{query}")
        ])
        
        # RAG pipeline: Query -> Retrieve (context) -> Generate Answer
        rag_chain = (
            # Passes query through, then retrieves context, then formats and generates
            RunnablePassthrough.assign(
                context=(lambda x: x["query"]) | self.retriever | (lambda docs: "\n\n---\n\n".join([doc.page_content for doc in docs]))
            )
            | rag_prompt
            | self.llm_generator
        )
        
        # --- 3.3 Direct LLM Chain (for general queries) ---
        llm_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful and concise general knowledge assistant. Answer the user's question directly."),
            ("human", "{query}")
        ])
        
        # Direct pipeline: Query -> Prompt -> Generate Answer
        direct_llm_chain = llm_prompt | self.llm_generator

        # --- 3.4 Combine into RunnableBranch (Router) ---
        # FIX: The conditional branch must be a tuple: (condition, runnable)
        return (
            RunnablePassthrough.assign(
                classification=intent_chain | (lambda x: x.content.strip()) 
            )
            | RunnableBranch(
                # Condition: If classification is 'RAG', execute rag_chain
                (
                    (lambda x: x["classification"].upper() == "RAG"), 
                    rag_chain
                ),
                # Default path: If classification is 'LLM' or anything else
                direct_llm_chain
            )
        )

    def __call__(self, query: str) -> Dict[str, Any]:
        """Runs the hybrid chain with the given query."""
        logger.info(f"Processing query: '{query}'")
        
        # We need to run the full chain and extract the final response
        result = self.chain.invoke({"query": query})
        
        # The result of the RunnableBranch is the final LLM response object
        # Note: 'classification' here currently just returns the response content
        return {
            "query": query,
            "response": result.content,
            "classification": result.content 
        }
