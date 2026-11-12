"""RAG service for document retrieval and context building."""
from typing import List, Optional
from services.vector_store import query_document_async as query_document
from services.chunking_service import chunk_text


async def build_rag_context(document_id: str, query: str, n_results: int = 5) -> str:
    """Build RAG context from document chunks.
    
    Returns:
        Formatted context string with retrieved chunks
    """
    results = await query_document(document_id, query, n_results=n_results)
    
    if not results:
        return "No relevant context found in the document."
    
    context_parts = []
    for i, result in enumerate(results):
        context_parts.append(f"[Retrieved Section {i+1}]\n{result['text']}")
    
    return "\n\n---\n\n".join(context_parts)


async def prepare_document_for_rag(document_id: str, text: str) -> dict:
    """Prepare a document for RAG by chunking and storing embeddings.
    
    Returns:
        Dictionary with chunk statistics
    """
    # Chunk the text
    chunks = chunk_text(text, chunk_size=1000, overlap=200, min_chunk_size=300)
    
    # Store in vector database
    from services.vector_store import create_document_collection_async
    count = await create_document_collection_async(document_id, chunks)
    
    return {
        'chunk_count': count,
        'chunks': chunks
    }


async def get_relevant_clauses(document_id: str, clause_queries: List[str], n_per_query: int = 3) -> List[dict]:
    """Get relevant document sections for multiple clause queries."""
    all_results = []
    seen_texts = set()
    
    for query in clause_queries:
        results = await query_document(document_id, query, n_results=n_per_query)
        for r in results:
            # Deduplicate by text
            text_key = r['text'][:100]
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                all_results.append(r)
    
    return all_results
