#!/usr/bin/env python3
"""
Cricket News Ingestion Script

Fetches cricket news from GNews API and stores in ChromaDB with embeddings

Usage:
    python data_pipelines/news/ingest.py --max 50
    python data_pipelines/news/ingest.py --max 100 --from-date 2024-01-01T00:00:00Z
"""

import argparse
import yaml
from datetime import datetime

from cricket_intelligence.core.embeddings import embed_batch
from cricket_intelligence.core.chromadb import get_collection, add_articles, get_count
from cricket_intelligence.core.news_client import fetch_news
from cricket_intelligence.config import settings
from cricket_intelligence.logging_config import get_logger

# Setup logging
logger = get_logger(__name__)

# Config
CONFIG_PATH = settings.cricket_news_config



def load_config():
    """Load cricket keywords from config"""
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


def fetch_cricket_news(api_key, max_articles=10, from_date=None):
    """
    Fetch cricket news using multiple keywords from config

    Args:
        api_key: GNews API key
        max_articles: Max articles to fetch (default: 10)
        from_date: Start date (ISO format)

    Returns:
        List of article dicts
    """
    config = load_config()
    keywords = config.get("keywords", [])

    print(f"Fetching cricket news using {len(keywords)} keyword queries...")

    all_articles = []
    articles_per_keyword = max(1, max_articles // len(keywords))

    for keyword in keywords:
        print(f"  Querying: {keyword}")

        # Use generic news fetcher
        result = fetch_news(api_key, keyword, articles_per_keyword, from_date)

        if "error" in result:
            print(f"    Error: {result['error']}")
            continue

        # Collect articles
        for article in result.get("articles", []):
            all_articles.append(article)
            print(f"    Found: {article['title'][:60]}...")

    # Deduplicate by URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article["url"] not in seen_urls:
            seen_urls.add(article["url"])
            unique_articles.append(article)

    print(f"\nFetched {len(unique_articles)} unique articles (from {len(all_articles)} total)")
    return unique_articles[:max_articles]


def ingest_to_chromadb(articles):
    """
    Create embeddings and store articles in ChromaDB

    Args:
        articles: List of article dicts

    Returns:
        Number of articles stored
    """
    if not articles:
        print("No articles to ingest")
        return 0

    # Create embeddings
    print(f"\nCreating embeddings for {len(articles)} articles...")
    texts = [f"{a['title']} {a['description']}" for a in articles]
    embeddings = embed_batch(texts)
    print(f"Created {len(embeddings)} embeddings (384-dim)")

    # Store in ChromaDB
    print("Storing in ChromaDB...")
    collection = get_collection()
    count = add_articles(articles, embeddings, collection)

    return count


def main():
    """Main ingestion pipeline"""
    parser = argparse.ArgumentParser(description="Ingest cricket news into ChromaDB")
    parser.add_argument("--max", type=int, default=10, help="Max articles to fetch (default: 20)")
    parser.add_argument("--from-date", type=str, help="Fetch from date (ISO format: 2024-01-01T00:00:00Z)")
    args = parser.parse_args()

    # Get API key
    api_key = os.getenv("GNEWS_API")
    if not api_key:
        print("Error: GNEWS_API environment variable not set!")
        print("Please set it in your .env file")
        sys.exit(1)

    # Show current stats
    print("=" * 60)
    print("Cricket News Ingestion")
    print("=" * 60)
    collection = get_collection()
    before_count = get_count(collection)
    print(f"Current ChromaDB article count: {before_count}\n")

    # Fetch news
    articles = fetch_cricket_news(api_key, max_articles=args.max, from_date=args.from_date)

    if not articles:
        print("\nNo articles found. Exiting.")
        sys.exit(0)

    # Ingest to ChromaDB
    added_count = ingest_to_chromadb(articles)

    # Final stats
    after_count = get_count(collection)
    print(f"\n" + "=" * 60)
    print("Ingestion Complete!")
    print("=" * 60)
    print(f"Articles processed: {len(articles)}")
    print(f"Articles added: {added_count}")
    print(f"Total articles in ChromaDB: {after_count}")
    print(f"New articles: {after_count - before_count}")


if __name__ == "__main__":
    main()
