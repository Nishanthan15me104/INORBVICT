import os
import sys
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# --- HARDCODED RAG CONFIGURATION ---
# These values are pulled from the original config.py to eliminate the import dependency.
RAG_EMBEDDING_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
RAG_CHUNK_SIZE = 256
# -----------------------------------

# --- FIX for ModuleNotFoundError: Dynamically add project root to Python path ---
# Since setup_rag.py is inside the 'chatbotapi' directory, we must go up one level (.parent.parent) 
# to find the true project root (C:\Documents\assign_chatbot).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Ensure the project root is at the beginning of the path for proper module resolution
if str(PROJECT_ROOT) not in sys.path:
    # Adding the root is essential for finding 'chatbotapi'
    sys.path.insert(0, str(PROJECT_ROOT))
# --------------------------------------------------------------------------------

# Load environment variables from .env file (if present)
load_dotenv()

# Set up logging for a clean output
# Logs will now be created directly in the project root
logger.add(os.path.join(PROJECT_ROOT, "file_{time}.log"), rotation="10 MB", level="INFO")
logger.info("Starting RAG Vector Store Setup...")

# Import the necessary components using the full project path
# NOTE: Removed dependency on chatbotapi.src.chat.config import settings
from chatbotapi.src.chat.application.long_term_memory_creation import LongTermMemoryCreator, ExtractionTarget

# --- Hardcoded Target Setup ---
target_name = "Jordan Peterson"
target_urls = [
    "https://plato.stanford.edu/entries/kant/", 
    "https://www.jordanbpeterson.com/" 
]

TARGET_ENTITY = ExtractionTarget()
TARGET_ENTITY.name = target_name
TARGET_ENTITY.urls = target_urls
# ------------------------------

# --- Persistence Configuration ---
FAISS_INDEX_PATH = "faiss_index"
# ---------------------------------


def setup_rag_index() -> None:
    """Orchestrates the creation and persistence of the RAG index using FAISS."""
    try:
        # 1. Build the Creator (Initializes models, splitter, and FAISS store)
        # NOTE: This method must now implicitly use the hardcoded values defined above, 
        # or it assumes the necessary RAG components are initialized correctly.
        creator = LongTermMemoryCreator.build_from_settings()
        
        # 2. Run the pipeline: Extract -> Chunk -> Deduplicate -> Embed -> Store in FAISS
        creator(TARGET_ENTITY)
        
        logger.success("RAG Vector Store Creation COMPLETE.")

        # 3. Persist the FAISS index to disk
        if hasattr(creator.retriever, 'vectorstore'):
            # Ensure the save path is relative to the project root
            save_path = os.path.join(PROJECT_ROOT, FAISS_INDEX_PATH)
            logger.info(f"Saving FAISS index locally to directory: {save_path}")
            creator.retriever.vectorstore.save_local(save_path)
            logger.success("FAISS index saved successfully.")
        else:
            logger.warning(
                "Could not access 'vectorstore' attribute on retriever for saving. "
                "The index remains in memory for this session."
            )
        
    except Exception as e:
        logger.error(f"An error occurred during RAG setup: {e}")
        # Log hardcoded config details instead of using the settings object
        logger.debug(f"RAG Settings: {RAG_EMBEDDING_MODEL_ID}, {RAG_CHUNK_SIZE}")
        
if __name__ == "__main__":
    setup_rag_index()
