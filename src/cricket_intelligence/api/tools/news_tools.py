"""
Cricket News Tools

Atomic tools for cricket news access via ChromaDB and GNews API.
LLM orchestrates these tools for smart fallback behavior.

Tools:
1. search_chromadb - Vector search in ChromaDB
2. query_cricket_articles - Query GNews API and auto-ingest to ChromaDB
"""

from cricket_intelligence.core.embeddings import embed_text, embed_batch
from cricket_intelligence.core.chromadb import get_collection, search, add_articles
from cricket_intelligence.core.news_client import fetch_news
from cricket_intelligence.config import settings
from cricket_intelligence.logging_config import get_logger

# Setup logging
logger = get_logger(__name__)


def search_chromadb(query: str, top_k: int = 5) -> dict:
    """
    Search ChromaDB for cricket news using semantic similarity

    Args:
        query: Search query
        top_k: Number of results to return

    Returns:
        Dict with query, results_count, and results
    """
    collection = get_collection()
    query_embedding = embed_text(query)
    results = search(query_embedding, top_k=top_k, collection=collection)

    return {
        "query": query,
        "results_count": len(results),
        "results": results
    }


def query_cricket_articles(query: str, max_articles: int = 10) -> dict:
    """
    Query cricket news from GNews API and automatically ingest to ChromaDB

    This function:
    1. Fetches articles from GNews API using generic fetcher
    2. Creates embeddings (title + description)
    3. Automatically ingests to ChromaDB with metadata (matches data pipeline)
    4. Returns the articles

    Args:
        query: Search query
        max_articles: Max articles to fetch (default: 10)

    Returns:
        Dict with query, articles_count, articles_added, and articles
    """
    api_key = settings.gnews_api_key
    if not api_key:
        return {"error": "GNEWS_API_KEY environment variable not set"}

    # Use generic news fetcher with cricket-specific query
    cricket_query = f"cricket AND ({query})"
    result = fetch_news(api_key, cricket_query, max_articles)

    if "error" in result:
        return result

    articles = result.get("articles", [])

    # Auto-ingest to ChromaDB (same as data pipeline)
    articles_added = 0
    if articles:
        # Create embeddings from title + description
        texts = [f"{a['title']} {a['description']}" for a in articles]
        embeddings = embed_batch(texts)

        # Store in ChromaDB (add_articles handles all metadata automatically)
        collection = get_collection()
        articles_added = add_articles(articles, embeddings, collection)

    return {
        "query": query,
        "articles_count": len(articles),
        "articles_added": articles_added,
        "articles": articles
    }
