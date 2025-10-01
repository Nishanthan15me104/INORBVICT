from typing import List
from langchain_community.document_loaders import WebBaseLoader, WikipediaLoader
from langchain_core.documents import Document
from tqdm import tqdm
from loguru import logger

# NOTE: Removed all philoagents.domain imports. Hardcoding the target name.

def extract_data_for_target(target_name: str, extract_urls: list[str]) -> list[Document]:
    """Extract documents for a single target from specified sources (Wikipedia and Stanford URL placeholder).

    Args:
        target_name: The name of the person/entity to search for (e.g., "Jordan Peterson").
        extract_urls: List of URLs to extract content from (used to simulate Stanford entries).

    Returns:
        list[Document]: List of documents extracted for the target.
    """
    
    # We use a placeholder ID as we are no longer using the Philosopher domain model
    target_id = target_name.lower().replace(" ", "-") 
    
    docs = []
    logger.info(f"Extracting data for target: {target_name} (ID: {target_id})")

    # 1. Extract from Wikipedia
    docs.extend(extract_wikipedia(target_name, target_id))
    
    # 2. Extract from specified Web URLs (Simulating the previous Stanford Encyclopedia source)
    # Filter URLs to only include Stanford example, or use the list provided if the user manually curated it.
    # For this example, we will just pass the provided URLs to the simplified extractor.
    docs.extend(extract_stanford_encyclopedia_of_philosophy(target_name, target_id, extract_urls))

    return docs


def extract_wikipedia(target_name: str, target_id: str) -> list[Document]:
    """Extract documents for the target from Wikipedia."""

    logger.info(f"Starting Wikipedia extraction for '{target_name}'.")

    loader = WikipediaLoader(
        query=target_name,
        lang="en",
        load_max_docs=1,
        doc_content_chars_max=1000000,
    )
    docs = loader.load()

    for doc in docs:
        doc.metadata["target_id"] = target_id
        doc.metadata["target_name"] = target_name
        doc.metadata["source_type"] = "Wikipedia"

    logger.success(f"Extracted {len(docs)} documents from Wikipedia.")
    return docs


def extract_stanford_encyclopedia_of_philosophy(
    target_name: str, target_id: str, urls: list[str]
) -> list[Document]:
    """Extract documents for a single philosopher from Stanford Encyclopedia of Philosophy (Simulated).

    We simulate the extraction from specific, curated web sources. Since you only want 
    Wikipedia and Stanford, we'll assume the 'urls' list *only* contains the required Stanford URLs 
    (or similar highly structured academic content).
    
    NOTE: The original complex scraping logic has been removed as it requires Beautiful Soup
    which might be complex to maintain. We will rely on the standard WebBaseLoader.

    Args:
        target_name: The name of the person/entity.
        target_id: The ID of the person/entity.
        urls: List of URLs to extract content from.

    Returns:
        list[Document]: List of documents extracted.
    """
    
    # We will manually filter the provided URLs to only allow stanford.edu links for demonstration
    # In a real setup, you would have a more robust filter.
    stanford_urls = [url for url in urls if "stanford.edu" in url or "plato.stanford.edu" in url]

    if not stanford_urls:
        logger.warning("No valid Stanford Encyclopedia URLs provided.")
        return []

    logger.info(f"Starting Stanford URL extraction for {len(stanford_urls)} sources.")
    
    loader = WebBaseLoader(stanford_urls, show_progress=False)
    
    documents = []
    
    with tqdm(stanford_urls, desc="Scraping Stanford URLs", unit="url", ncols=100) as pbar:
        for url in pbar:
            try:
                docs = loader.load_documents([url]) 
                for doc in docs:
                    text = doc.page_content.strip()
                    if not text:
                        continue
                        
                    doc.metadata["source"] = url
                    doc.metadata["target_id"] = target_id
                    doc.metadata["target_name"] = target_name
                    doc.metadata["source_type"] = "Stanford Encyclopedia (Web)"
                    doc.page_content = text
                    documents.append(doc)
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
                
    logger.success(f"Extracted {len(documents)} documents from Stanford Encyclopedia.")
    return documents


if __name__ == "__main__":
    # Example usage:
    target_name = "Jordan Peterson"
    target_id = target_name.lower().replace(" ", "-")
    # Example academic URL to test the flow
    example_urls = [
        "https://plato.stanford.edu/entries/kant/", # Example Stanford page
        "https://www.jordanbpeterson.com/podcast-list/", # This URL will be ignored by the simple filter above
    ]
    
    docs = extract_data_for_target(target_name, example_urls)
    
    # Print the first document for verification
    if docs:
        print(f"\n--- Extracted Document Example ---")
        print(f"Source: {docs[0].metadata.get('source', 'N/A')}")
        print(f"Content Start: {docs[0].page_content[:200]}...")
