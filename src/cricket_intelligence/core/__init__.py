"""Core Utilities - Shared functionality across the system"""

from cricket_intelligence.core.embeddings import embed_text, embed_batch
from cricket_intelligence.core.chromadb import (
    get_client,
    get_collection,
    add_articles,
    search,
    get_count,
    delete_collection,
)
from cricket_intelligence.core.news_client import fetch_news

__all__ = [
    "embed_text",
    "embed_batch",
    "get_client",
    "get_collection",
    "add_articles",
    "search",
    "get_count",
    "delete_collection",
    "fetch_news",
]
