from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

# Updated local import


Splitter = RecursiveCharacterTextSplitter


def get_splitter(chunk_size: int) -> Splitter:

    """Returns a token-based text splitter with overlap.

    Args:
        chunk_size: Number of tokens for each text chunk.

    Returns:
        Splitter: A configured text splitter instance that
            splits text into overlapping chunks based on token count.
    """

    # 15% overlap is a common heuristic
    chunk_overlap = int(0.15 * chunk_size)

    logger.info(
        f"Getting splitter with chunk size: {chunk_size} and overlap: {chunk_overlap}"
    )

    # Uses a specific tokenizer ("cl100k_base") for token counting
    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
