#!/usr/bin/env python3
"""
Basic Integration Test for Cricket Intelligence Agent

Tests the full agent flow: MCP connection → Query → Response
"""

import os
import sys
import asyncio
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent can be created and initialized"""
    print("\n" + "="*60)
    print("Test 1: Agent Initialization")
    print("="*60)

    from cricket_intelligence.agent.cricket_agent import CricketAgent

    agent = CricketAgent()
    print("✓ Agent created")

    await agent.initialize()
    print("✓ Agent initialized with MCP connection")

    await agent.close()
    print("✓ Agent closed cleanly")

    return True


@pytest.mark.asyncio
async def test_sql_query():
    """Test SQL-based cricket stats query"""
    print("\n" + "="*60)
    print("Test 2: SQL Stats Query")
    print("="*60)

    from cricket_intelligence.agent.cricket_agent import CricketAgent

    agent = CricketAgent()
    await agent.initialize()

    query = "Who are the top 3 run scorers in Test cricket?"
    print(f"\nQuery: {query}")

    result = await agent.chat(query)

    print(f"\n✓ Response received: {result['response'][:100]}...")

    insight = result.get('insight', {})
    assert insight.get('query_type') in ['stats', 'mixed'], "Should be stats or mixed query"
    assert len(result['response']) > 0, "Should have non-empty response"

    print(f"✓ Query type: {insight.get('query_type')}")
    print(f"✓ Confidence: {insight.get('confidence')}")

    if insight.get('insights'):
        print(f"✓ Generated {len(insight['insights'])} insights")

    await agent.close()

    return True


@pytest.mark.asyncio
async def test_news_query():
    """Test news search query"""
    print("\n" + "="*60)
    print("Test 3: News Search Query")
    print("="*60)

    from cricket_intelligence.agent.cricket_agent import CricketAgent

    agent = CricketAgent()
    await agent.initialize()

    query = "Latest cricket news"
    print(f"\nQuery: {query}")

    result = await agent.chat(query)

    print(f"\n✓ Response received: {result['response'][:100]}...")

    insight = result.get('insight', {})
    # News query might return empty if no news in DB, that's ok
    print(f"✓ Query type: {insight.get('query_type')}")

    await agent.close()

    return True


async def run_all_tests():
    """Run all agent tests"""
    print("\n" + "="*70)
    print(" "*20 + "Cricket Agent Integration Tests")
    print("="*70)

    # Check prerequisites
    if not os.getenv("OPENAI_API"):
        print("\n❌ OPENAI_API not found in .env file")
        print("Please set it before running tests")
        return False

    print("\n✓ Prerequisites checked")

    # Run tests
    tests = [
        ("Agent Initialization", test_agent_initialization),
        ("SQL Query", test_sql_query),
        ("News Query", test_news_query),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ Test '{test_name}' failed:")
            print(f"   Error: {str(e)}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "="*70)
    print(f"Test Summary: {passed} passed, {failed} failed")
    print("="*70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
