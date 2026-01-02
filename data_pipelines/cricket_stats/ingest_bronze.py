"""
Bronze Layer: Test Cricket Data Ingestion

Loads raw Test cricket CSV data (1877-2024) into Bronze DuckDB
Source: Kaggle Test Cricket Dataset

Usage:
    python data_pipelines/cricket_stats/ingest_bronze.py
"""

import os
import duckdb
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CSV_DIR = PROJECT_ROOT / "data" / "csv_data"
DB_PATH = PROJECT_ROOT / "data" / "duck_db" / "bronze" / "cricket_stats.duckdb"


def ingest_data():
    """Load Test cricket CSVs into DuckDB"""

    print("="*60)
    print("Test Cricket Data Ingestion to DuckDB")
    print("="*60)

    # Check CSV directory
    if not CSV_DIR.exists():
        print(f"Error: {CSV_DIR} not found!")
        return

    # List CSV files
    csv_files = {
        "players": CSV_DIR / "players_info.csv",
        "matches": CSV_DIR / "test_Matches_Data.csv",
        "batting": CSV_DIR / "test_Batting_Card.csv",
        "bowling": CSV_DIR / "test_Bowling_Card.csv",
        "fow": CSV_DIR / "test_Fow_Card.csv",
        "partnerships": CSV_DIR / "test_Partnership_Card.csv"
    }

    # Connect to DuckDB
    print(f"\nCreating database: {DB_PATH}")
    conn = duckdb.connect(str(DB_PATH))

    # Drop existing tables
    print("Dropping existing tables...")
    conn.execute("DROP TABLE IF EXISTS partnerships")
    conn.execute("DROP TABLE IF EXISTS fall_of_wickets")
    conn.execute("DROP TABLE IF EXISTS bowling_performances")
    conn.execute("DROP TABLE IF EXISTS batting_performances")
    conn.execute("DROP TABLE IF EXISTS matches")
    conn.execute("DROP TABLE IF EXISTS players")

    # Load players
    print("\n1. Loading players...")
    conn.execute(f"""
        CREATE TABLE players AS
        SELECT * FROM read_csv_auto('{csv_files["players"]}')
    """)
    players_count = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    print(f"   Loaded {players_count:,} players")

    # Load matches
    print("\n2. Loading matches...")
    conn.execute(f"""
        CREATE TABLE matches AS
        SELECT * FROM read_csv_auto('{csv_files["matches"]}')
    """)
    matches_count = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    print(f"   Loaded {matches_count:,} matches")

    # Load batting performances
    print("\n3. Loading batting performances...")
    conn.execute(f"""
        CREATE TABLE batting_performances AS
        SELECT * FROM read_csv_auto('{csv_files["batting"]}')
    """)
    batting_count = conn.execute("SELECT COUNT(*) FROM batting_performances").fetchone()[0]
    print(f"   Loaded {batting_count:,} batting performances")

    # Load bowling performances
    print("\n4. Loading bowling performances...")
    conn.execute(f"""
        CREATE TABLE bowling_performances AS
        SELECT * FROM read_csv_auto('{csv_files["bowling"]}')
    """)
    bowling_count = conn.execute("SELECT COUNT(*) FROM bowling_performances").fetchone()[0]
    print(f"   Loaded {bowling_count:,} bowling performances")

    # Load fall of wickets (if exists)
    if csv_files["fow"].exists():
        print("\n5. Loading fall of wickets...")
        conn.execute(f"""
            CREATE TABLE fall_of_wickets AS
            SELECT * FROM read_csv_auto('{csv_files["fow"]}')
        """)
        fow_count = conn.execute("SELECT COUNT(*) FROM fall_of_wickets").fetchone()[0]
        print(f"   Loaded {fow_count:,} fall of wicket records")

    # Load partnerships (if exists)
    if csv_files["partnerships"].exists():
        print("\n6. Loading partnerships...")
        conn.execute(f"""
            CREATE TABLE partnerships AS
            SELECT * FROM read_csv_auto('{csv_files["partnerships"]}')
        """)
        part_count = conn.execute("SELECT COUNT(*) FROM partnerships").fetchone()[0]
        print(f"   Loaded {part_count:,} partnership records")

    # Create indexes
    print("\n7. Creating indexes...")
    conn.execute("CREATE INDEX idx_player_id ON players(player_id)")
    conn.execute("CREATE INDEX idx_match_id ON matches(\"Match ID\")")
    conn.execute("CREATE INDEX idx_batting_match ON batting_performances(\"Match ID\")")
    conn.execute("CREATE INDEX idx_bowling_match ON bowling_performances(\"Match ID\")")
    print("   Indexes created")

    # Final stats
    print("\n" + "="*60)
    print("Ingestion Complete!")
    print("="*60)
    print(f"Database: {DB_PATH}")
    print(f"Players: {players_count:,}")
    print(f"Matches: {matches_count:,}")
    print(f"Batting records: {batting_count:,}")
    print(f"Bowling records: {bowling_count:,}")

    conn.close()


if __name__ == "__main__":
    # Run ingestion
    ingest_data()

    # Test queries
    print("\n" + "="*60)
    print("Running Test Queries")
    print("="*60)

    conn = duckdb.connect(str(DB_PATH))

    # Query 1: Top run scorers
    print("\nQuery 1: Top 10 Run Scorers (All Time)")
    print("-" * 60)
    result = conn.execute("""
        SELECT
            p.player_name,
            COUNT(DISTINCT b."Match ID") as matches,
            SUM(b.runs) as total_runs,
            ROUND(AVG(b.runs), 2) as avg_runs,
            MAX(b.runs) as high_score
        FROM batting_performances b
        JOIN players p ON b.batsman = p.player_id
        WHERE b.runs IS NOT NULL
        GROUP BY p.player_name
        HAVING COUNT(DISTINCT b."Match ID") >= 20
        ORDER BY total_runs DESC
        LIMIT 10
    """).fetchall()

    for player, matches, runs, avg, high in result:
        print(f"{player:30s} | {int(runs):6,} runs | {matches:3d} matches | avg: {avg:6.2f} | high: {int(high):3d}")

    # Query 2: Recent matches
    print("\nQuery 2: Most Recent 5 Matches")
    print("-" * 60)
    result = conn.execute("""
        SELECT
            "Match Start Date",
            "Team1 Name",
            "Team2 Name",
            "Match Winner",
            "Match Venue (Stadium)"
        FROM matches
        ORDER BY "Match Start Date" DESC
        LIMIT 5
    """).fetchall()

    for date, team1, team2, winner, venue in result:
        print(f"{date} | {team1:15s} vs {team2:15s}")
        print(f"{'':12s} Winner: {winner:15s} | Venue: {venue}")
        print()

    print("\nTest queries completed successfully!")
