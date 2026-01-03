#!/usr/bin/env python3
"""
Test Cricket Stats Pipeline

Tests the cricket stats ingestion and transformation:
- Bronze layer: Raw data ingestion from CSV
- Silver layer: Clean, standardized data

Usage:
    python tests/test_stats_pipeline.py
"""

import os
import sys
from pathlib import Path
import duckdb

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Database paths
BRONZE_DB = PROJECT_ROOT / "data" / "duck_db" / "bronze" / "cricket_stats.duckdb"
SILVER_DB = PROJECT_ROOT / "data" / "duck_db" / "silver" / "cricket_stats.duckdb"


def test_bronze_database():
    """Test Bronze database schema and data"""
    print("=" * 60)
    print("Test 1: Bronze Database")
    print("=" * 60)

    if not BRONZE_DB.exists():
        print(f"❌ Bronze database not found at: {BRONZE_DB}")
        print("Run: python data_pipelines/cricket_stats/ingest_bronze.py")
        return False

    conn = duckdb.connect(str(BRONZE_DB), read_only=True)

    # Check tables exist
    expected_tables = ['players', 'matches', 'batting_performances',
                       'bowling_performances', 'fall_of_wickets', 'partnerships']

    tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
    actual_tables = [row[0] for row in conn.execute(tables_query).fetchall()]

    print(f"Expected tables: {len(expected_tables)}")
    print(f"Found tables: {len(actual_tables)}")

    for table in expected_tables:
        if table in actual_tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  ✓ {table}: {count:,} rows")
        else:
            print(f"  ❌ {table}: NOT FOUND")
            conn.close()
            return False

    # Test sample query (Bronze has raw column names)
    print("\nSample Query: Top 5 run scorers")
    query = """
        SELECT
            p.player_name,
            SUM(b.runs) as total_runs
        FROM batting_performances b
        JOIN players p ON b.batsman = p.player_id
        GROUP BY p.player_name
        ORDER BY total_runs DESC
        LIMIT 5
    """
    results = conn.execute(query).fetchall()
    for i, (player, runs) in enumerate(results, 1):
        print(f"  {i}. {player}: {runs:,} runs")

    conn.close()
    return True


def test_silver_database():
    """Test Silver database schema and data"""
    print("\n" + "=" * 60)
    print("Test 2: Silver Database")
    print("=" * 60)

    if not SILVER_DB.exists():
        print(f"❌ Silver database not found at: {SILVER_DB}")
        print("Run: python data_pipelines/cricket_stats/transform_silver.py")
        return False

    conn = duckdb.connect(str(SILVER_DB), read_only=True)

    # Check tables exist
    expected_tables = ['players', 'matches', 'batting', 'bowling',
                       'fall_of_wickets', 'partnerships']

    tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
    actual_tables = [row[0] for row in conn.execute(tables_query).fetchall()]

    print(f"Expected tables: {len(expected_tables)}")
    print(f"Found tables: {len(actual_tables)}")

    for table in expected_tables:
        if table in actual_tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  ✓ {table}: {count:,} rows")
        else:
            print(f"  ❌ {table}: NOT FOUND")
            conn.close()
            return False

    # Test cleaned column names (no spaces, camelCase standardized)
    print("\nVerifying cleaned schema (batting table):")
    schema_query = "PRAGMA table_info(batting)"
    columns = conn.execute(schema_query).fetchall()

    print(f"  Columns ({len(columns)}):")
    for col in columns[:5]:  # Show first 5 columns
        print(f"    - {col[1]} ({col[2]})")

    # Test sample query with cleaned names
    print("\nSample Query: Top 5 strike rates (min 500 runs)")
    query = """
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
    results = conn.execute(query).fetchall()
    for i, (player, runs, balls, sr) in enumerate(results, 1):
        print(f"  {i}. {player}: {runs:,} runs @ {sr} SR")

    conn.close()
    return True


def test_bronze_to_silver_consistency():
    """Test data consistency between Bronze and Silver"""
    print("\n" + "=" * 60)
    print("Test 3: Bronze → Silver Consistency")
    print("=" * 60)

    if not BRONZE_DB.exists() or not SILVER_DB.exists():
        print("❌ Both databases must exist")
        return False

    bronze_conn = duckdb.connect(str(BRONZE_DB), read_only=True)
    silver_conn = duckdb.connect(str(SILVER_DB), read_only=True)

    # Compare row counts
    print("Comparing row counts:")

    table_mappings = [
        ('players', 'players'),
        ('matches', 'matches'),
        ('batting_performances', 'batting'),
        ('bowling_performances', 'bowling'),
        ('fall_of_wickets', 'fall_of_wickets'),
        ('partnerships', 'partnerships')
    ]

    all_match = True
    for bronze_table, silver_table in table_mappings:
        bronze_count = bronze_conn.execute(f"SELECT COUNT(*) FROM {bronze_table}").fetchone()[0]
        silver_count = silver_conn.execute(f"SELECT COUNT(*) FROM {silver_table}").fetchone()[0]

        match = "✓" if bronze_count == silver_count else "❌"
        print(f"  {match} {bronze_table} → {silver_table}: {bronze_count:,} → {silver_count:,}")

        if bronze_count != silver_count:
            all_match = False

    bronze_conn.close()
    silver_conn.close()

    return all_match


def test_sample_analytics_queries():
    """Test analytics queries on Silver database"""
    print("\n" + "=" * 60)
    print("Test 4: Sample Analytics Queries")
    print("=" * 60)

    if not SILVER_DB.exists():
        print("❌ Silver database not found")
        return False

    conn = duckdb.connect(str(SILVER_DB), read_only=True)

    # Query 1: Player stats
    print("Query 1: Top batting performances (single match)")
    query1 = """
        SELECT p.name, b.runs, b.balls_faced, b.match_id
        FROM batting b
        JOIN players p ON b.player_id = p.player_id
        ORDER BY b.runs DESC
        LIMIT 5
    """
    results = conn.execute(query1).fetchall()
    for i, row in enumerate(results, 1):
        print(f"  {i}. {row[0]}: {row[1]} runs ({row[2]} balls) - Match {row[3]}")

    # Query 2: Best bowling figures
    print("\nQuery 2: Best bowling figures (single match)")
    query2 = """
        SELECT p.name, b.wickets, b.runs_conceded, b.match_id
        FROM bowling b
        JOIN players p ON b.player_id = p.player_id
        WHERE b.wickets > 0
        ORDER BY b.wickets DESC, b.runs_conceded ASC
        LIMIT 5
    """
    results = conn.execute(query2).fetchall()
    for i, row in enumerate(results, 1):
        print(f"  {i}. {row[0]}: {row[1]}/{row[2]} - Match {row[3]}")

    # Query 3: Match statistics
    print("\nQuery 3: Recent matches")
    query3 = """
        SELECT match_id, start_date, team1, team2, winner
        FROM matches
        ORDER BY start_date DESC
        LIMIT 5
    """
    results = conn.execute(query3).fetchall()
    for i, row in enumerate(results, 1):
        print(f"  {i}. {row[1]}: {row[2]} vs {row[3]} (Winner: {row[4]})")

    conn.close()
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Cricket Stats Pipeline Tests")
    print("=" * 60 + "\n")

    tests = [
        ("Bronze Database", test_bronze_database),
        ("Silver Database", test_silver_database),
        ("Bronze → Silver Consistency", test_bronze_to_silver_consistency),
        ("Sample Analytics Queries", test_sample_analytics_queries)
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
        print("\nNote: If databases don't exist, run:")
        print("  python data_pipelines/cricket_stats/ingest_bronze.py")
        print("  python data_pipelines/cricket_stats/transform_silver.py")

    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
