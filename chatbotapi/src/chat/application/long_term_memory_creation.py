from langchain_core.documents import Document
from loguru import logger
from typing import List

from chatbotapi.src.chat.application.data.duplicate_documents import deduplicate_documents
from chatbotapi.src.chat.application.rag.retrievers import Retriever, get_retriever
from chatbotapi.src.chat.application.rag.splitters import Splitter, get_splitter

# NOTE: We are replacing PhilosopherExtract domain with a hardcoded string
# The extraction generator logic is now handled internally in extracts.py

# A simple class representing the single entity to extract data for
class ExtractionTarget:
    """Placeholder for the target entity to ensure structure consistency."""
    name: str = "Jordan Peterson"
    # Example academic URL to ensure the Stanford filter in extracts.py is tested
    urls: List[str] = ["https://plato.stanford.edu/entries/kant/"] 

# We will use FAISS which manages the vector store directly

class LongTermMemoryCreator:
    def __init__(self, retriever: Retriever, splitter: Splitter) -> None:
        self.retriever = retriever
        self.splitter = splitter

    @classmethod
    def build_from_settings(cls) -> "LongTermMemoryCreator":

        """Initializes the creator with settings-based retriever and splitter."""
        retriever = get_retriever(
            embedding_model_id='sentence-transformers/all-MiniLM-L6-v2',
            k=3,
            device="cpu",
        )
        splitter = get_splitter(chunk_size= 256)

        return cls(retriever, splitter)

    def __call__(self, extraction_target: ExtractionTarget) -> None:
        """
        Runs the extraction, chunking, deduplication, and vector store addition process.
        
        Args:
            extraction_target: The single hardcoded entity to extract data for.
        """
        logger.info(f"Starting memory creation for: {extraction_target.name}")

        # The extraction generator now simplifies the process to a single call
        # We need to manually import the specific function from the extracts module
        from chatbotapi.src.chat.application.data.extract import extract_data_for_target
        
        docs = extract_data_for_target(extraction_target.name, extraction_target.urls)

        if not docs:
            logger.warning("No documents extracted. Exiting.")
            return

        logger.info(f"Extracted {len(docs)} documents. Starting chunking and embedding.")
        
        # 1. Chunk documents
        chunked_docs = self.splitter.split_documents(docs)
        logger.info(f"Documents split into {len(chunked_docs)} chunks.")

        # 2. Deduplicate
        chunked_docs = deduplicate_documents(chunked_docs, threshold=0.7)
        logger.info(f"{len(chunked_docs)} unique chunks remaining after deduplication.")
        
        # 3. Add to FAISS Vector Store (this handles embedding internally)
        # NOTE: If FAISS was loaded from disk, this step will append new documents. 
        # For a full refresh, you'd clear the index first, but for this RAG setup, 
        # we assume it's a one-time setup run via setup_rag.py.
        self.retriever.vectorstore.add_documents(chunked_docs)
        logger.success("Long-Term Memory (FAISS Vector Store) created/updated successfully.")


class LongTermMemoryRetriever:
    def __init__(self, retriever: Retriever) -> None:
        self.retriever = retriever

    @classmethod
    def build_from_settings(cls, embedding_model_id: str, chunk_size: int):

        """Initializes the retriever with settings."""
        retriever = get_retriever(
            embedding_model_id="sentence-transformers/all-MiniLM-L6-v2",
            k=3,
            device="cpu",
        )
        return cls(retriever)

    def __call__(self, query: str) -> list[Document]:
        from chatbotapi.src.chat.config import settings
        """Invokes the retriever to get relevant documents for a query."""
        logger.info(f"Retrieving top 3 documents for query: {query}")
        # FAISS retriever is invoked directly
        return self.retriever.invoke(query)

if __name__ == "__main__":
    # Example usage:
    # NOTE: In a real scenario, this would be triggered by a setup script
    creator = LongTermMemoryCreator.build_from_settings(
        embedding_model_id="sentence-transformers/all-MiniLM-L6-v2", 
        chunk_size=256
    )
    creator(ExtractionTarget())
