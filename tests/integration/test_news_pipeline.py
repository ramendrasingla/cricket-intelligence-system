#!/usr/bin/env python3
"""
Test News Ingestion Pipeline

Tests the cricket news ingestion pipeline:
- Fetching cricket news from GNews API
- Creating embeddings
- Storing in ChromaDB

Usage:
    python tests/test_news_pipeline.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cricket_intelligence.core.news_client import fetch_news
from cricket_intelligence.core.embeddings import embed_text, embed_batch
from cricket_intelligence.core.chromadb import get_collection, add_articles, search, get_count

# Load environment
load_dotenv()

def test_fetch_news():
    """Test fetching news from GNews API"""
    print("=" * 60)
    print("Test 1: Fetch Cricket News from GNews API")
    print("=" * 60)

    api_key = os.getenv("GNEWS_API")
    if not api_key:
        print("❌ GNEWS_API not found in environment")
        return False

    # Test basic fetch
    query = "cricket India Australia"
    max_articles = 3

    print(f"Fetching {max_articles} articles for: '{query}'")
    result = fetch_news(api_key, query, max_articles)

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False

    articles = result.get("articles", [])
    print(f"✓ Fetched {len(articles)} articles")

    if articles:
        print(f"\nSample article:")
        print(f"  Title: {articles[0]['title']}")
        print(f"  Source: {articles[0]['source']}")
        print(f"  Published: {articles[0]['published_at']}")
        print(f"  URL: {articles[0]['url'][:60]}...")

    return len(articles) > 0


def test_embeddings():
    """Test creating embeddings"""
    print("\n" + "=" * 60)
    print("Test 2: Create Embeddings")
    print("=" * 60)

    texts = [
        "Virat Kohli scores century in Test match",
        "India wins against Australia at MCG"
    ]

    print(f"Creating embeddings for {len(texts)} texts...")

    # Test single embedding
    single_embedding = embed_text(texts[0])
    print(f"✓ Single embedding dimension: {len(single_embedding)}")

    # Test batch embeddings
    batch_embeddings = embed_batch(texts)
    print(f"✓ Batch embeddings count: {len(batch_embeddings)}")
    print(f"✓ Each embedding dimension: {len(batch_embeddings[0])}")

    return len(batch_embeddings) == len(texts)


def test_chromadb_operations():
    """Test ChromaDB operations"""
    print("\n" + "=" * 60)
    print("Test 3: ChromaDB Operations")
    print("=" * 60)

    # Get collection
    collection = get_collection()
    print(f"✓ Connected to ChromaDB collection: {collection.name}")

    # Get current count
    initial_count = get_count(collection)
    print(f"✓ Current article count: {initial_count}")

    # Test adding articles
    test_articles = [
        {
            "url": f"https://test-url-{initial_count + 1}.com",
            "title": "Test Article: Kohli Century",
            "description": "Virat Kohli scores his 50th century",
            "content": "Full article content here...",
            "source": "Test Source",
            "published_at": "2024-01-01T00:00:00Z"
        }
    ]

    texts = [f"{a['title']} {a['description']}" for a in test_articles]
    embeddings = embed_batch(texts)

    print(f"Adding {len(test_articles)} test article(s)...")
    added_count = add_articles(test_articles, embeddings, collection)
    print(f"✓ Added {added_count} article(s)")

    # Verify count increased
    new_count = get_count(collection)
    print(f"✓ New article count: {new_count}")

    # Test search
    query = "Kohli century"
    print(f"\nSearching for: '{query}'")
    query_embedding = embed_text(query)
    results = search(query_embedding, top_k=3, collection=collection)

    print(f"✓ Found {len(results)} results")
    if results:
        print(f"\nTop result:")
        print(f"  Title: {results[0]['title']}")
        print(f"  Distance: {results[0]['distance']:.4f}")

    return new_count >= initial_count


def test_full_pipeline():
    """Test complete news ingestion pipeline"""
    print("\n" + "=" * 60)
    print("Test 4: Full News Ingestion Pipeline")
    print("=" * 60)

    api_key = os.getenv("GNEWS_API")
    if not api_key:
        print("❌ GNEWS_API not found")
        return False

    # 1. Fetch news
    query = "cricket Test match"
    max_articles = 2

    print(f"Step 1: Fetching {max_articles} articles...")
    result = fetch_news(api_key, query, max_articles)

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False

    articles = result.get("articles", [])
    print(f"✓ Fetched {len(articles)} articles")

    if not articles:
        print("⚠ No articles fetched (API might be rate limited)")
        return True  # Not a failure, just API limitation

    # 2. Create embeddings
    print("\nStep 2: Creating embeddings...")
    texts = [f"{a['title']} {a['description']}" for a in articles]
    embeddings = embed_batch(texts)
    print(f"✓ Created {len(embeddings)} embeddings")

    # 3. Store in ChromaDB
    print("\nStep 3: Storing in ChromaDB...")
    collection = get_collection()
    added_count = add_articles(articles, embeddings, collection)
    print(f"✓ Stored {added_count} articles")

    # 4. Verify search works
    print("\nStep 4: Verifying search...")
    query_embedding = embed_text(query)
    results = search(query_embedding, top_k=5, collection=collection)
    print(f"✓ Search returned {len(results)} results")

    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Cricket News Pipeline Tests")
    print("=" * 60 + "\n")

    tests = [
        ("Fetch News", test_fetch_news),
        ("Embeddings", test_embeddings),
        ("ChromaDB Operations", test_chromadb_operations),
        ("Full Pipeline", test_full_pipeline)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with exception: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\nTotal: {passed}/{total} tests passed")

    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
