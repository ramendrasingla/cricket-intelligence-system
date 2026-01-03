"""
Silver Layer: Test Cricket Data Transformation

Transforms Bronze layer into clean, standardized Silver layer
- Standardizes column names (remove spaces, parentheses)
- Cleans data types
- Adds calculated fields
- Creates clean schema for analytical queries

Usage:
    python data_pipelines/cricket_stats/transform_silver.py
"""

import duckdb

from cricket_intelligence.config import settings
from cricket_intelligence.logging_config import get_logger

# Setup logging
logger = get_logger(__name__)

# Paths from config
BRONZE_DB = settings.project_root / "data" / "duck_db" / "bronze" / "cricket_stats.duckdb"
SILVER_DB = settings.silver_db_path


def transform_to_silver():
    """Transform Bronze to Silver layer with clean schema"""

    logger.info("=" * 60)
    logger.info("Test Cricket Bronze → Silver Transformation")
    logger.info("=" * 60)

    # Check Bronze DB exists
    if not BRONZE_DB.exists():
        logger.info(f"Error: Bronze database not found at {BRONZE_DB}")
        logger.info("Please run data_pipelines/cricket_stats/ingest_bronze.py first")
        return

    # Connect to Bronze (read-only)
    logger.info(f"\nReading from Bronze: {BRONZE_DB}")
    bronze_conn = duckdb.connect(str(BRONZE_DB), read_only=True)

    # Connect to Silver (create/overwrite)
    logger.info(f"Writing to Silver: {SILVER_DB}")
    silver_conn = duckdb.connect(str(SILVER_DB))

    # Attach Bronze DB to access it from Silver
    silver_conn.execute(f"ATTACH '{BRONZE_DB}' AS bronze (READ_ONLY)")

    # Drop existing Silver tables
    logger.info("\nDropping existing Silver tables...")
    silver_conn.execute("DROP TABLE IF EXISTS partnerships")
    silver_conn.execute("DROP TABLE IF EXISTS fall_of_wickets")
    silver_conn.execute("DROP TABLE IF EXISTS bowling")
    silver_conn.execute("DROP TABLE IF EXISTS batting")
    silver_conn.execute("DROP TABLE IF EXISTS matches")
    silver_conn.execute("DROP TABLE IF EXISTS players")

    # Transform Players
    logger.info("\n1. Transforming players table...")
    silver_conn.execute("""
        CREATE TABLE players AS
        SELECT
            player_id,
            player_name AS name,
            country_id,
            batting_style,
            bowling_style,
            gender,
            dob,
            dod
        FROM bronze.players
    """)

    count = silver_conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    logger.info(f"   Created players table: {count:,} rows")

    # Transform Matches
    logger.info("\n2. Transforming matches table...")
    silver_conn.execute("""
        CREATE TABLE matches AS
        SELECT
            "Match ID" AS match_id,
            "Team1 Name" AS team1,
            "Team2 Name" AS team2,
            "Match Winner" AS winner,
            "Match Result Text" AS result_text,
            "Match Start Date" AS start_date,
            "Match End Date" AS end_date,
            "Match Venue (Stadium)" AS stadium,
            "Match Venue (City)" AS city,
            "Match Venue (Country)" AS country,
            "Toss Winner" AS toss_winner,
            "Toss Winner Choice" AS toss_choice,
            "MOM Player" AS mom_player_id,
            "Innings1 Team1 Runs Scored" AS innings1_team1_runs,
            "Innings1 Team1 Wickets Fell" AS innings1_team1_wickets,
            "Innings1 Team2 Runs Scored" AS innings1_team2_runs,
            "Innings1 Team2 Wickets Fell" AS innings1_team2_wickets,
            "Innings2 Team1 Runs Scored" AS innings2_team1_runs,
            "Innings2 Team1 Wickets Fell" AS innings2_team1_wickets,
            "Innings2 Team2 Runs Scored" AS innings2_team2_runs,
            "Innings2 Team2 Wickets Fell" AS innings2_team2_wickets
        FROM bronze.matches
    """)

    count = silver_conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    logger.info(f"   Created matches table: {count:,} rows")

    # Transform Batting Performances
    logger.info("\n3. Transforming batting performances...")
    silver_conn.execute("""
        CREATE TABLE batting AS
        SELECT
            "Match ID" AS match_id,
            batsman AS player_id,
            runs,
            balls AS balls_faced,
            fours,
            sixes,
            strikeRate AS strike_rate,
            innings,
            team,
            isOut AS is_out,
            wicketType AS wicket_type,
            fielders,
            bowler AS bowler_id
        FROM bronze.batting_performances
    """)

    count = silver_conn.execute("SELECT COUNT(*) FROM batting").fetchone()[0]
    logger.info(f"   Created batting table: {count:,} rows")

    # Transform Bowling Performances
    logger.info("\n4. Transforming bowling performances...")
    silver_conn.execute("""
        CREATE TABLE bowling AS
        SELECT
            "Match ID" AS match_id,
            "bowler id" AS player_id,
            overs,
            maidens,
            conceded AS runs_conceded,
            wickets,
            economy,
            innings,
            team,
            opposition
        FROM bronze.bowling_performances
    """)

    count = silver_conn.execute("SELECT COUNT(*) FROM bowling").fetchone()[0]
    logger.info(f"   Created bowling table: {count:,} rows")

    # Transform Fall of Wickets (if exists)
    fow_exists = bronze_conn.execute("""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_name = 'fall_of_wickets'
    """).fetchone()[0] > 0

    if fow_exists:
        logger.info("\n5. Transforming fall of wickets...")
        silver_conn.execute("""
            CREATE TABLE fall_of_wickets AS
            SELECT
                "Match ID" AS match_id,
                innings,
                team,
                player AS player_id,
                wicket AS wicket_number,
                over,
                runs AS runs_at_fall
            FROM bronze.fall_of_wickets
        """)

        count = silver_conn.execute("SELECT COUNT(*) FROM fall_of_wickets").fetchone()[0]
        logger.info(f"   Created fall_of_wickets table: {count:,} rows")

    # Transform Partnerships (if exists)
    part_exists = bronze_conn.execute("""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_name = 'partnerships'
    """).fetchone()[0] > 0

    if part_exists:
        logger.info("\n6. Transforming partnerships...")
        silver_conn.execute("""
            CREATE TABLE partnerships AS
            SELECT
                "Match ID" AS match_id,
                innings,
                team,
                opposition,
                "for wicket" AS wicket,
                player1 AS player1_id,
                player2 AS player2_id,
                "player1 runs" AS player1_runs,
                "player2 runs" AS player2_runs,
                "player1 balls" AS player1_balls,
                "player2 balls" AS player2_balls,
                "partnership runs" AS runs,
                "partnership balls" AS balls
            FROM bronze.partnerships
        """)

        count = silver_conn.execute("SELECT COUNT(*) FROM partnerships").fetchone()[0]
        logger.info(f"   Created partnerships table: {count:,} rows")

    # Create indexes
    logger.info("\n7. Creating indexes...")
    silver_conn.execute("CREATE INDEX idx_players_id ON players(player_id)")
    silver_conn.execute("CREATE INDEX idx_players_name ON players(name)")
    silver_conn.execute("CREATE INDEX idx_matches_id ON matches(match_id)")
    silver_conn.execute("CREATE INDEX idx_matches_date ON matches(start_date)")
    silver_conn.execute("CREATE INDEX idx_batting_match ON batting(match_id)")
    silver_conn.execute("CREATE INDEX idx_batting_player ON batting(player_id)")
    silver_conn.execute("CREATE INDEX idx_bowling_match ON bowling(match_id)")
    silver_conn.execute("CREATE INDEX idx_bowling_player ON bowling(player_id)")

    if fow_exists:
        silver_conn.execute("CREATE INDEX idx_fow_match ON fall_of_wickets(match_id)")

    if part_exists:
        silver_conn.execute("CREATE INDEX idx_part_match ON partnerships(match_id)")

    logger.info("   Indexes created")

    # Get final stats
    player_count = silver_conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    match_count = silver_conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    batting_count = silver_conn.execute("SELECT COUNT(*) FROM batting").fetchone()[0]
    bowling_count = silver_conn.execute("SELECT COUNT(*) FROM bowling").fetchone()[0]

    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("Transformation Complete!")
    logger.info("=" * 60)
    logger.info(f"Silver Database: {SILVER_DB}")
    logger.info(f"\nTable Statistics:")
    logger.info(f"  Players: {player_count:,}")
    logger.info(f"  Matches: {match_count:,}")
    logger.info(f"  Batting records: {batting_count:,}")
    logger.info(f"  Bowling records: {bowling_count:,}")

    if fow_exists:
        fow_count = silver_conn.execute("SELECT COUNT(*) FROM fall_of_wickets").fetchone()[0]
        logger.info(f"  Fall of wickets: {fow_count:,}")

    if part_exists:
        part_count = silver_conn.execute("SELECT COUNT(*) FROM partnerships").fetchone()[0]
        logger.info(f"  Partnerships: {part_count:,}")

    # Close connections
    bronze_conn.close()
    silver_conn.close()


if __name__ == "__main__":
    # Run transformation
    transform_to_silver()

    # Test query on Silver layer
    logger.info("\n" + "=" * 60)
    logger.info("Running Test Query on Silver Layer")
    logger.info("=" * 60)

    conn = duckdb.connect(str(SILVER_DB))

    # Query: Best partnership from away team in most recent IND vs AUS match in Australia
    logger.info("\nQuery: Best Partnership (Away Team) - Most Recent IND vs AUS in Australia")
    logger.info("-" * 60)

    # Find most recent India vs Australia match in Australia
    match_result = conn.execute("""
        SELECT
            match_id,
            start_date,
            team1,
            team2,
            stadium,
            country
        FROM matches
        WHERE
            ((team1 = 'India' AND team2 = 'Australia')
             OR (team1 = 'Australia' AND team2 = 'India'))
            AND country = 'Australia'
        ORDER BY start_date DESC
        LIMIT 1
    """).fetchone()

    if match_result:
        match_id, date, team1, team2, stadium, country = match_result
        away_team = 'India'  # India is away in Australia

        logger.info(f"Match: {team1} vs {team2} on {date}")
        logger.info(f"Venue: {stadium}, {country}")
        logger.info(f"Away Team: {away_team}\n")

        # Find best partnership
        partnership_result = conn.execute("""
            SELECT
                innings,
                player1_id,
                player2_id,
                runs,
                balls
            FROM partnerships
            WHERE match_id = ?
              AND team = ?
            ORDER BY runs DESC
            LIMIT 1
        """, [match_id, away_team]).fetchone()

        if partnership_result:
            innings, bat1, bat2, runs, balls = partnership_result

            # Get player names
            player1_name = conn.execute("SELECT name FROM players WHERE player_id = ?", [bat1]).fetchone()
            player2_name = conn.execute("SELECT name FROM players WHERE player_id = ?", [bat2]).fetchone()

            logger.info(f"Best Partnership (Innings {innings}):")
            if player1_name:
                logger.info(f"  Player 1: {player1_name[0]} (ID: {bat1})")
            else:
                logger.info(f"  Player 1 ID: {bat1}")

            if player2_name:
                logger.info(f"  Player 2: {player2_name[0]} (ID: {bat2})")
            else:
                logger.info(f"  Player 2 ID: {bat2}")

            logger.info(f"  Runs: {runs}")
            logger.info(f"  Balls: {balls}")
        else:
            logger.info("No partnership data found for this match")
    else:
        logger.info("No India vs Australia match found in Australia")

    conn.close()
    logger.info("\nTest query completed successfully!")
