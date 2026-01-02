#!/usr/bin/env python3
"""
Simple ChromaDB Manager
Store and search news articles with embeddings
"""

import chromadb
from chromadb.config import Settings
import os

# Paths
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
COLLECTION_NAME = "cricket_news_articles"


def get_client():
    """Get ChromaDB client (creates DB directory if needed)"""
    os.makedirs(DB_PATH, exist_ok=True)

    client = chromadb.PersistentClient(
        path=DB_PATH,
        settings=Settings(anonymized_telemetry=False)
    )
    return client


def get_collection(client=None):
    """Get or create the news articles collection"""
    if client is None:
        client = get_client()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Cricket news articles"}
    )
    return collection


def add_articles(articles: list[dict], embeddings, collection=None):
    """
    Add articles to ChromaDB

    Args:
        articles: List of dicts with keys: url, title, description, content, source, published_at
        embeddings: numpy array of embeddings (shape: len(articles) x 384)
        collection: ChromaDB collection (optional)

    Returns: Number of articles added
    """
    if collection is None:
        collection = get_collection()

    if not articles:
        return 0

    # Prepare data
    ids = []
    documents = []
    metadatas = []

    for i, article in enumerate(articles):
        # Use URL as ID (clean it up)
        article_id = article.get("url", f"article_{i}").replace("/", "_").replace(":", "_")
        ids.append(article_id)

        # Full text for document
        full_text = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"
        documents.append(full_text.strip())

        # Metadata
        metadata = {
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "source": article.get("source", ""),
            "published_at": article.get("published_at", ""),
            "description": article.get("description", "")
        }
        metadatas.append(metadata)

    # Add to collection (auto-handles duplicates by ID)
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings.tolist()
    )

    return len(articles)


def search(query_embedding, top_k: int = 5, collection=None):
    """
    Search for similar articles

    Args:
        query_embedding: numpy array (384-dim)
        top_k: Number of results
        collection: ChromaDB collection (optional)

    Returns: List of article dicts with metadata and distance scores
    """
    if collection is None:
        collection = get_collection()

    # Query ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )

    # Format results
    articles = []
    if results and results["ids"] and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            article = {
                "id": results["ids"][0][i],
                "title": results["metadatas"][0][i].get("title", ""),
                "url": results["metadatas"][0][i].get("url", ""),
                "source": results["metadatas"][0][i].get("source", ""),
                "published_at": results["metadatas"][0][i].get("published_at", ""),
                "description": results["metadatas"][0][i].get("description", ""),
                "distance": results["distances"][0][i] if "distances" in results else None
            }
            articles.append(article)

    return articles


def get_count(collection=None):
    """Get number of articles in collection"""
    if collection is None:
        collection = get_collection()

    return collection.count()


def delete_collection():
    """Delete the collection (careful!)"""
    client = get_client()
    try:
        client.delete_collection(name=COLLECTION_NAME)
        return True
    except:
        return False


if __name__ == "__main__":
    # Quick test
    print("Testing ChromaDB Manager...")

    collection = get_collection()
    print(f"Collection: {collection.name}")
    print(f"Article count: {get_count(collection)}")

    print("ChromaDB Manager ready!")
