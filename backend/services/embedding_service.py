"""Embedding service using sentence-transformers."""
import os
import numpy as np
from typing import List, Optional, Union
from sentence_transformers import SentenceTransformer

# Set model cache directory
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parent.parent
os.environ['HF_HOME'] = str(BACKEND_DIR / 'model_cache')
os.environ['TRANSFORMERS_CACHE'] = str(BACKEND_DIR / 'model_cache')

# Global model instance (lazy loaded) - with type hint
_model: Optional[SentenceTransformer] = None


def get_model() -> SentenceTransformer:
    """Get or initialize the embedding model."""
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def generate_embeddings(texts: List[str]) -> np.ndarray:
    """Generate embeddings for a list of texts.
    
    Returns:
        numpy array of shape (len(texts), 384)
    """
    model = get_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings


def generate_embedding(text: str) -> np.ndarray:
    """Generate embedding for a single text.
    
    Returns:
        numpy array of shape (384,)
    """
    model = get_model()
    embedding = model.encode([text], convert_to_numpy=True)[0]
    return embedding


def compute_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """Compute cosine similarity between two embeddings."""
    return float(np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2)))
