"""Vector store service using ChromaDB."""
import os
import asyncio
from functools import partial
import chromadb
from chromadb.config import Settings
from typing import List, Optional, Dict, Any
import numpy as np

from core.config import CHROMA_PERSIST_DIR
from services.embedding_service import generate_embedding, generate_embeddings

# Ensure directory exists
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

# Global client instance - initialized to None with type hint
_client: Optional[chromadb.PersistentClient] = None


def get_client() -> chromadb.PersistentClient:
    """Get or initialize the ChromaDB client."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return _client


def get_collection_name(document_id: str) -> str:
    """Generate collection name for a document."""
    # ChromaDB collection names must be 3-63 chars, alphanumeric with underscores
    return f"doc_{document_id.replace('-', '_')[:50]}"


_THREAD_POOL = None


def _get_thread_pool():
    global _THREAD_POOL
    if _THREAD_POOL is None:
        from concurrent.futures import ThreadPoolExecutor
        _THREAD_POOL = ThreadPoolExecutor(max_workers=2)
    return _THREAD_POOL


async def create_document_collection_async(document_id: str, chunks: List[dict], metadatas: Optional[List[dict]] = None) -> int:
    """Async wrapper for create_document_collection."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _get_thread_pool(),
        partial(create_document_collection, document_id, chunks, metadatas)
    )


async def query_document_async(document_id: str, query: str, n_results: int = 5) -> List[dict]:
    """Async wrapper for query_document."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _get_thread_pool(),
        partial(query_document, document_id, query, n_results)
    )


def create_document_collection(document_id: str, chunks: List[dict], metadatas: Optional[List[dict]] = None) -> int:
    """Create a vector collection for a document.
    
    Args:
        document_id: The document ID
        chunks: List of chunk dictionaries with 'text' key
        metadatas: Optional list of metadata dicts for each chunk
    
    Returns:
        Number of chunks stored
    """
    client = get_client()
    collection_name = get_collection_name(document_id)
    
    # Delete existing collection if present
    try:
        client.delete_collection(collection_name)
    except Exception as e:
        # Collection doesn't exist, which is fine
        pass
    
    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Generate embeddings
    texts = [c['text'] for c in chunks]
    embeddings = generate_embeddings(texts)
    
    # Prepare IDs and metadatas
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    if metadatas is None:
        metadatas = [{'chunk_index': i, 'char_count': c.get('char_count', len(c['text']))} for i, c in enumerate(chunks)]
    
    # Add to collection
    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=metadatas
    )
    
    return len(chunks)


def query_document(document_id: str, query: str, n_results: int = 5) -> List[dict]:
    """Query a document's vector collection.
    
    Returns:
        List of result dictionaries with text, metadata, and distance
    """
    client = get_client()
    collection_name = get_collection_name(document_id)
    
    try:
        collection = client.get_collection(collection_name)
    except Exception as e:
        print(f"Collection not found: {e}")
        return []
    
    # Generate query embedding
    query_embedding = generate_embedding(query)
    
    # Query collection
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=n_results
    )
    
    # Format results
    formatted = []
    if results['documents'] and results['documents'][0]:
        for i, doc in enumerate(results['documents'][0]):
            formatted.append({
                'text': doc,
                'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                'distance': results['distances'][0][i] if results['distances'] else 0,
                'id': results['ids'][0][i] if results['ids'] else f"chunk_{i}"
            })
    
    return formatted


def delete_document_collection(document_id: str):
    """Delete a document's vector collection."""
    client = get_client()
    collection_name = get_collection_name(document_id)
    try:
        client.delete_collection(collection_name)
    except Exception as e:
        # Collection doesn't exist
        print(f"Could not delete collection: {e}")


def collection_exists(document_id: str) -> bool:
    """Check if a document collection exists."""
    client = get_client()
    collection_name = get_collection_name(document_id)
    try:
        client.get_collection(collection_name)
        return True
    except Exception:
        return False
