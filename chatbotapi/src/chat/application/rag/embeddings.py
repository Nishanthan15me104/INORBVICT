from langchain_huggingface import HuggingFaceEmbeddings

EmbeddingsModel = HuggingFaceEmbeddings


# 1. DEFINE THE HELPER FUNCTION FIRST
def get_huggingface_embedding_model(
    model_id: str, device: str
) -> HuggingFaceEmbeddings:
    """Gets a HuggingFace embedding model instance."""
    # ... (function body)
    return HuggingFaceEmbeddings(
        model_name=model_id,
        model_kwargs={"device": device, "trust_remote_code": True},
        encode_kwargs={"normalize_embeddings": False},
    )


# 2. DEFINE THE WRAPPER FUNCTION SECOND (Now it can see the helper)
def get_embedding_model(
    model_id: str,
    device: str = "cpu",
) -> EmbeddingsModel:
    """Gets an instance of a HuggingFace embedding model."""
    # This call will now succeed!
    return get_huggingface_embedding_model(model_id, device)