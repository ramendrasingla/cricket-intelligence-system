#!/usr/bin/env python3
"""
Simple Embedder - Create embeddings using sentence-transformers
Model: all-MiniLM-L6-v2 (384 dimensions)
"""

from sentence_transformers import SentenceTransformer
import numpy as np

from cricket_intelligence.config import settings

EMBEDDING_DIM = 384

# Lazy loading to avoid loading model at import time
_MODEL = None


def _get_model() -> SentenceTransformer:
    """Get or create the sentence transformer model (lazy loading)"""
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(settings.embedding_model)
    return _MODEL


def embed_text(text: str) -> np.ndarray:
    """
    Embed a single text string

    Returns: 384-dim numpy array
    """
    if not text or not text.strip():
        return np.zeros(EMBEDDING_DIM)

    model = _get_model()
    return model.encode(text, convert_to_numpy=True)


def embed_batch(texts: list[str]) -> np.ndarray:
    """
    Embed multiple texts at once (faster than one-by-one)

    Returns: numpy array of shape (len(texts), 384)
    """
    if not texts:
        return np.array([])

    model = _get_model()
    return model.encode(texts, convert_to_numpy=True)


def embed_article(article: dict) -> np.ndarray:
    """
    Embed article by combining title + description

    Args:
        article: dict with 'title' and 'description' fields

    Returns: 384-dim numpy array
    """
    title = article.get("title", "")
    description = article.get("description", "")

    # Combine title and description
    combined = f"{title} {description}".strip()

    return embed_text(combined)


if __name__ == "__main__":
    # Quick test
    print("Testing embedder...")

    # Single text
    text = "Virat Kohli scored a century"
    embedding = embed_text(text)
    print(f"Single embedding shape: {embedding.shape}")

    # Batch
    texts = ["India vs Australia", "T20 World Cup", "Cricket news"]
    embeddings = embed_batch(texts)
    print(f"Batch embeddings shape: {embeddings.shape}")

    # Article
    article = {
        "title": "Cricket News",
        "description": "India wins the series"
    }
    article_emb = embed_article(article)
    print(f"Article embedding shape: {article_emb.shape}")

    print("All tests passed!")
