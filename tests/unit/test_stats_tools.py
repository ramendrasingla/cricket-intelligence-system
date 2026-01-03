#!/usr/bin/env python3
"""
Test Cricket Stats MCP Tools

Tests the MCP tools for cricket statistics:
- get_database_schema: Get DuckDB schema info
- execute_sql: Execute SQL queries
- get_sample_queries: Get example queries

Usage:
    python tests/test_stats_tools.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cricket_intelligence.api.tools.stats_tools import (
    get_database_schema,
    execute_sql,
    get_sample_queries
)

# Database path
SILVER_DB = PROJECT_ROOT / "data" / "duck_db" / "silver" / "cricket_stats.duckdb"


def test_get_database_schema():
    """Test get_database_schema tool"""
    print("=" * 60)
    print("Test 1: get_database_schema")
    print("=" * 60)

    if not SILVER_DB.exists():
        print(f"❌ Silver database not found at: {SILVER_DB}")
        print("Run: python data_pipelines/cricket_stats/transform_silver.py")
        return False

    # Test getting all tables
    print("Getting schema for all tables...")
    result = get_database_schema()

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False

    print(f"✓ Database: {result['database']}")
    print(f"✓ Tables found: {len(result['tables'])}")

    for table_info in result['tables']:
        print(f"\n  Table: {table_info['table_name']}")
        print(f"    Rows: {table_info['row_count']:,}")
        print(f"    Columns: {len(table_info['columns'])}")
        # Show first 3 columns
        for col in table_info['columns'][:3]:
            print(f"      - {col['name']} ({col['type']})")

    # Test getting specific table
    print("\n" + "-" * 60)
    print("Getting schema for 'batting' table...")
    result_batting = get_database_schema(table_name="batting")

    if "error" in result_batting:
        print(f"❌ Error: {result_batting['error']}")
        return False

    print(f"✓ Tables returned: {len(result_batting['tables'])}")
    if result_batting['tables']:
        batting_info = result_batting['tables'][0]
        print(f"✓ Table: {batting_info['table_name']}")
        print(f"✓ Columns: {len(batting_info['columns'])}")

    return True


def test_execute_sql():
    """Test execute_sql tool"""
    print("\n" + "=" * 60)
    print("Test 2: execute_sql")
    print("=" * 60)

    if not SILVER_DB.exists():
        print(f"❌ Silver database not found")
        return False

    # Test 1: Simple aggregation query
    print("Query 1: Top 5 run scorers")
    query1 = """
        SELECT p.name, SUM(b.runs) as total_runs
        FROM batting b
        JOIN players p ON b.player_id = p.player_id
        GROUP BY p.name
        ORDER BY total_runs DESC
        LIMIT 5
    """

    result1 = execute_sql(sql=query1)

    if "error" in result1:
        print(f"❌ Error: {result1['error']}")
        return False

    print(f"✓ Query executed successfully")
    print(f"✓ Rows returned: {result1['row_count']}")
    print(f"✓ Columns: {result1['columns']}")

    print("\nResults:")
    for i, row in enumerate(result1['rows'], 1):
        print(f"  {i}. {row['name']}: {row['total_runs']:,} runs")

    # Test 2: More complex query
    print("\n" + "-" * 60)
    print("Query 2: Best strike rates (min 500 runs)")
    query2 = """
        SELECT
            p.name,
            SUM(b.runs) as total_runs,
            SUM(b.balls_faced) as total_balls,
            ROUND(SUM(b.runs) * 100.0 / NULLIF(SUM(b.balls_faced), 0), 2) as strike_rate
        FROM batting b
        JOIN players p ON b.player_id = p.player_id
        WHERE b.balls_faced > 0
        GROUP BY p.name
        HAVING SUM(b.runs) >= 500
        ORDER BY strike_rate DESC
        LIMIT 5
    """

    result2 = execute_sql(sql=query2)

    if "error" in result2:
        print(f"❌ Error: {result2['error']}")
        return False

    print(f"✓ Rows returned: {result2['row_count']}")

    print("\nResults:")
    for i, row in enumerate(result2['rows'], 1):
        print(f"  {i}. {row['name']}: SR {row['strike_rate']} ({row['total_runs']:,} runs)")

    # Test 3: Invalid SQL (should handle gracefully)
    print("\n" + "-" * 60)
    print("Query 3: Invalid SQL (should fail gracefully)")
    query3 = "SELECT * FROM nonexistent_table"

    result3 = execute_sql(sql=query3)

    if "error" in result3:
        print(f"✓ Error handled correctly: {result3['error'][:60]}...")
        return True
    else:
        print(f"❌ Should have returned an error")
        return False


def test_get_sample_queries():
    """Test get_sample_queries tool"""
    print("\n" + "=" * 60)
    print("Test 3: get_sample_queries")
    print("=" * 60)

    if not SILVER_DB.exists():
        print(f"❌ Silver database not found")
        return False

    result = get_sample_queries()

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False

    print(f"✓ Database: {result['database']}")
    print(f"✓ Sample queries: {len(result['queries'])}")

    # Show each query category
    for query_info in result['queries']:
        print(f"\n  Category: {query_info['category']}")
        print(f"    Description: {query_info['description']}")
        print(f"    SQL: {query_info['sql'][:80]}...")

    return True


def test_real_world_queries():
    """Test real-world analytical queries"""
    print("\n" + "=" * 60)
    print("Test 4: Real-World Analytical Queries")
    print("=" * 60)

    if not SILVER_DB.exists():
        print(f"❌ Silver database not found")
        return False

    queries = [
        {
            "name": "Player Performance Summary",
            "sql": """
                SELECT
                    p.name,
                    COUNT(*) as matches,
                    SUM(b.runs) as total_runs,
                    ROUND(AVG(b.runs), 2) as avg_runs
                FROM batting b
                JOIN players p ON b.player_id = p.player_id
                GROUP BY p.name
                ORDER BY total_runs DESC
                LIMIT 3
            """
        },
        {
            "name": "Best Bowling Figures",
            "sql": """
                SELECT
                    p.name,
                    MAX(b.wickets) as best_wickets,
                    COUNT(*) as matches_bowled
                FROM bowling b
                JOIN players p ON b.player_id = p.player_id
                WHERE b.wickets > 0
                GROUP BY p.name
                ORDER BY best_wickets DESC
                LIMIT 3
            """
        },
        {
            "name": "Recent Matches",
            "sql": """
                SELECT
                    match_id,
                    start_date,
                    team1,
                    team2,
                    winner
                FROM matches
                ORDER BY start_date DESC
                LIMIT 3
            """
        }
    ]

    all_passed = True
    for query_info in queries:
        print(f"\n{query_info['name']}:")
        result = execute_sql(sql=query_info['sql'])

        if "error" in result:
            print(f"  ❌ Error: {result['error']}")
            all_passed = False
        else:
            print(f"  ✓ Success: {result['row_count']} row(s) returned")
            if result['rows']:
                # Show first result
                first_row = result['rows'][0]
                print(f"    Sample: {first_row}")

    return all_passed


def test_sql_injection_protection():
    """Test that SQL injection is prevented"""
    print("\n" + "=" * 60)
    print("Test 5: SQL Injection Protection")
    print("=" * 60)

    # Test DML (should be blocked)
    dangerous_queries = [
        "DROP TABLE batting",
        "DELETE FROM batting",
        "UPDATE batting SET runs = 0",
        "INSERT INTO batting VALUES (1, 2, 3)"
    ]

    all_blocked = True
    for dangerous_sql in dangerous_queries:
        result = execute_sql(sql=dangerous_sql)

        if "error" in result and ("not allowed" in result['error'].lower() or
                                   "only SELECT" in result['error']):
            print(f"✓ Blocked: {dangerous_sql}")
        else:
            print(f"❌ Should have blocked: {dangerous_sql}")
            all_blocked = False

    return all_blocked


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Cricket Stats MCP Tools Tests")
    print("=" * 60 + "\n")

    tests = [
        ("get_database_schema", test_get_database_schema),
        ("execute_sql", test_execute_sql),
        ("get_sample_queries", test_get_sample_queries),
        ("Real-World Queries", test_real_world_queries),
        ("SQL Injection Protection", test_sql_injection_protection)
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

    if not all(results.values()):
        print("\nNote: If database doesn't exist, run:")
        print("  python data_pipelines/cricket_stats/ingest_bronze.py")
        print("  python data_pipelines/cricket_stats/transform_silver.py")

    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
