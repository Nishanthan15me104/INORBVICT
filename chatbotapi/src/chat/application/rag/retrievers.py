import os
from langchain_community.vectorstores import FAISS
from langchain_core.retrievers import BaseRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from loguru import logger
from langchain_core.documents import Document 

# Updated local import


# Define the path where the FAISS index is expected to be saved
FAISS_INDEX_PATH = "faiss_index"

# We will use the BaseRetriever type, which FAISS's .as_retriever() returns
Retriever = BaseRetriever


def get_retriever(
    embedding_model_id: str,
    k: int = 3,
    device: str = "cpu",
) -> Retriever:
    """Creates and returns a FAISS-backed vector store retriever, loading from disk if available.

    Args:
        embedding_model_id (str): The identifier for the embedding model to use.
        k (int, optional): Number of documents to retrieve. Defaults to 3.
        device (str, optional): Device to run the embedding model on. Defaults to "cpu".

    Returns:
        Retriever: A configured FAISS vector store retriever.
    """
    logger.info(
        f"Initializing FAISS retriever | model: {embedding_model_id} | device: {device} | top_k: {k}"
    )
    from chatbotapi.src.chat.application.rag.embeddings import get_embedding_model
    embedding_model = get_embedding_model(embedding_model_id, device)

    # Check if the FAISS index has been persisted locally
    if os.path.exists(FAISS_INDEX_PATH):
        logger.info(f"FAISS index found at '{FAISS_INDEX_PATH}'. Loading index from disk.")
        # FIX: Corrected typo from 'FAFFS_INDEX_PATH' to 'FAISS_INDEX_PATH'
        vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embedding_model, allow_dangerous_deserialization=True)
    else:
        logger.warning(
            f"No FAISS index found at '{FAISS_INDEX_PATH}'. Creating a new in-memory index."
            f"This index will be empty until data is added."
        )
        # Create a temporary dummy index for initialization
        dummy_docs = [
            Document(page_content="initial faiss index placeholder for RAG setup", metadata={"source": "setup"}),
            Document(page_content="this document is temporary and will be overwritten", metadata={"source": "setup"})
        ]
        vectorstore = FAISS.from_documents(dummy_docs, embedding_model)

    # Return the retriever instance
    return vectorstore.as_retriever(search_kwargs={"k": k})
