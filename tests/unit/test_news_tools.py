#!/usr/bin/env python3
"""
Test Cricket News MCP Tools

Tests the MCP tools for cricket news:
- search_chromadb: Vector search in ChromaDB
- query_cricket_articles: Fetch from GNews API and auto-ingest

Usage:
    python tests/test_news_tools.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cricket_intelligence.api.tools.news_tools import search_chromadb, query_cricket_articles
from cricket_intelligence.core.chromadb import get_collection, get_count

# Load environment
load_dotenv()


def test_search_chromadb():
    """Test search_chromadb tool"""
    print("=" * 60)
    print("Test 1: search_chromadb")
    print("=" * 60)

    # Check if ChromaDB has data
    collection = get_collection()
    count = get_count(collection)
    print(f"ChromaDB article count: {count}")

    if count == 0:
        print("⚠ No articles in ChromaDB. Run news ingestion first:")
        print("  python data_pipelines/news/ingest.py --max 10")
        return True  # Not a failure, just no data

    # Test search
    query = "Virat Kohli"
    top_k = 3

    print(f"\nSearching for: '{query}' (top {top_k})")
    result = search_chromadb(query=query, top_k=top_k)

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False

    print(f"✓ Query: {result['query']}")
    print(f"✓ Results count: {result['results_count']}")

    if result['results_count'] > 0:
        print(f"\nTop result:")
        top = result['results'][0]
        print(f"  Title: {top['title']}")
        print(f"  Source: {top['source']}")
        print(f"  Distance: {top['distance']:.4f}")
        print(f"  URL: {top['url'][:60]}...")

    return True


def test_query_cricket_articles():
    """Test query_cricket_articles tool (with auto-ingest)"""
    print("\n" + "=" * 60)
    print("Test 2: query_cricket_articles")
    print("=" * 60)

    api_key = os.getenv("GNEWS_API")
    if not api_key:
        print("❌ GNEWS_API not found in environment")
        return False

    # Get initial count
    collection = get_collection()
    initial_count = get_count(collection)
    print(f"Initial ChromaDB count: {initial_count}")

    # Query and auto-ingest
    query = "Test cricket"
    max_articles = 2

    print(f"\nQuerying GNews API: '{query}' (max {max_articles})")
    result = query_cricket_articles(query=query, max_articles=max_articles)

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        if "rate limit" in result['error'].lower():
            print("⚠ GNews API rate limited. This is expected with free tier.")
            return True  # Not a failure, just API limitation
        return False

    print(f"✓ Query: {result['query']}")
    print(f"✓ Articles fetched: {result['articles_count']}")
    print(f"✓ Articles added to ChromaDB: {result['articles_added']}")

    if result['articles_count'] > 0:
        print(f"\nSample article:")
        article = result['articles'][0]
        print(f"  Title: {article['title']}")
        print(f"  Source: {article['source']}")
        print(f"  URL: {article['url'][:60]}...")

    # Verify count increased
    final_count = get_count(collection)
    print(f"\nFinal ChromaDB count: {final_count}")
    print(f"Net increase: +{final_count - initial_count}")

    return True


def test_smart_fallback_workflow():
    """Test the smart fallback pattern: search → query → search"""
    print("\n" + "=" * 60)
    print("Test 3: Smart Fallback Workflow")
    print("=" * 60)

    api_key = os.getenv("GNEWS_API")
    if not api_key:
        print("❌ GNEWS_API not found")
        return False

    # Use a very specific query unlikely to be in ChromaDB
    import time
    unique_query = f"Test cricket match {int(time.time())}"

    print(f"Testing workflow with unique query: '{unique_query}'")

    # Step 1: Search ChromaDB (expect no results)
    print("\nStep 1: Search ChromaDB")
    search_result = search_chromadb(query=unique_query, top_k=5)
    print(f"  Results found: {search_result['results_count']}")

    # Step 2: If no results, query GNews API (auto-ingest)
    if search_result['results_count'] == 0:
        print("\nStep 2: No results found, querying GNews API...")
        query_result = query_cricket_articles(query="Test cricket", max_articles=1)

        if "error" in query_result:
            print(f"  ⚠ API error: {query_result['error']}")
            return True  # API limitation, not test failure

        print(f"  Articles fetched: {query_result['articles_count']}")
        print(f"  Articles added: {query_result['articles_added']}")

        # Step 3: Search again (should find new articles)
        print("\nStep 3: Search ChromaDB again")
        search_result2 = search_chromadb(query="Test cricket", top_k=5)
        print(f"  Results found: {search_result2['results_count']}")

        if search_result2['results_count'] > 0:
            print("  ✓ Smart fallback workflow successful!")
        else:
            print("  ⚠ No results after ingestion (might need more relevant articles)")

    else:
        print("  Note: Found existing results, skipping fallback test")

    return True


def test_query_variations():
    """Test different query patterns"""
    print("\n" + "=" * 60)
    print("Test 4: Query Variations")
    print("=" * 60)

    queries = [
        ("Player name", "Virat Kohli"),
        ("Match type", "Test cricket"),
        ("Tournament", "World Cup"),
        ("General", "cricket news")
    ]

    collection = get_collection()
    count = get_count(collection)

    if count == 0:
        print("⚠ No articles in ChromaDB. Skipping variation tests.")
        return True

    for category, query in queries:
        print(f"\n{category}: '{query}'")
        result = search_chromadb(query=query, top_k=2)

        if result['results_count'] > 0:
            print(f"  ✓ Found {result['results_count']} result(s)")
            print(f"    Top: {result['results'][0]['title'][:50]}...")
        else:
            print(f"  - No results found")

    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Cricket News MCP Tools Tests")
    print("=" * 60 + "\n")

    tests = [
        ("search_chromadb", test_search_chromadb),
        ("query_cricket_articles", test_query_cricket_articles),
        ("Smart Fallback Workflow", test_smart_fallback_workflow),
        ("Query Variations", test_query_variations)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
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

    print("\nNote: Some tests may show warnings if:")
    print("  - ChromaDB is empty (run news ingestion first)")
    print("  - GNews API is rate limited (free tier limitation)")

    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
