"""
Cricket Stats Tools

Atomic tools for cricket statistics via DuckDB SQL.
LLM orchestrates these tools for Text2SQL functionality.

Tools:
1. get_database_schema - Get table schemas for Text2SQL
2. execute_sql - Execute raw SQL queries
3. get_sample_queries - Get example queries for reference
"""

import sys
from pathlib import Path
from typing import Optional
import duckdb
import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DML, DDL

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
SILVER_DB = PROJECT_ROOT / "data" / "duck_db" / "silver" / "cricket_stats.duckdb"


def _is_safe_sql(sql: str) -> tuple[bool, str]:
    """
    Validate that SQL query is safe (SELECT/WITH only, no DML/DDL)

    Args:
        sql: SQL query to validate

    Returns:
        Tuple of (is_safe, error_message)
    """
    # Parse SQL
    parsed = sqlparse.parse(sql)

    if not parsed:
        return False, "Empty or invalid SQL query"

    # Check each statement
    for statement in parsed:
        # Get the first meaningful token
        first_token = statement.token_first(skip_ws=True, skip_cm=True)

        if not first_token:
            continue

        # Get token type and value
        token_value = first_token.value.upper()

        # Allow SELECT and WITH (for CTEs)
        if token_value in ('SELECT', 'WITH'):
            # Check for forbidden keywords in the entire statement
            statement_upper = str(statement).upper()
            forbidden_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE',
                                  'ALTER', 'TRUNCATE', 'REPLACE', 'MERGE']

            for keyword in forbidden_keywords:
                if keyword in statement_upper:
                    return False, f"Forbidden keyword detected: {keyword}. only SELECT queries allowed."
        else:
            return False, f"only SELECT and WITH (CTE) statements allowed. Found: {token_value}"

    return True, ""


def get_database_schema(table_name: Optional[str] = None) -> dict:
    """
    Get database schema information

    Args:
        table_name: Optional specific table name, or None for all tables

    Returns:
        Dict with schema info (tables, columns, row counts)
    """
    if not SILVER_DB.exists():
        return {
            "error": f"Silver database not found at {SILVER_DB}",
            "hint": "Run data_pipelines/cricket_stats/transform_silver.py first"
        }

    conn = duckdb.connect(str(SILVER_DB), read_only=True)

    try:
        schema_info = {"database": str(SILVER_DB), "tables": []}

        if table_name:
            # Get specific table schema
            tables_to_query = [table_name]
        else:
            # Get all tables
            tables_to_query = ["players", "matches", "batting", "bowling", "fall_of_wickets", "partnerships"]

        for table in tables_to_query:
            try:
                columns = conn.execute(f"DESCRIBE {table}").fetchall()
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

                schema_info["tables"].append({
                    "table_name": table,
                    "columns": [{"name": col[0], "type": col[1]} for col in columns],
                    "row_count": count
                })
            except:
                pass

        return schema_info
    finally:
        conn.close()


def execute_sql(sql: str) -> dict:
    """
    Execute SQL query on cricket database

    Args:
        sql: SQL query to execute (SELECT only, read-only)

    Returns:
        Dict with query results
    """
    if not SILVER_DB.exists():
        return {
            "error": f"Silver database not found at {SILVER_DB}",
            "hint": "Run data_pipelines/cricket_stats/transform_silver.py first"
        }

    # Validate SQL safety
    is_safe, error_msg = _is_safe_sql(sql)
    if not is_safe:
        return {
            "error": error_msg,
            "sql": sql
        }

    conn = duckdb.connect(str(SILVER_DB), read_only=True)

    try:
        # Execute query
        result = conn.execute(sql).fetchall()

        # Get column names
        column_names = [desc[0] for desc in conn.description] if conn.description else []

        # Convert to list of dicts
        rows = []
        for row in result:
            row_dict = {}
            for i, col_name in enumerate(column_names):
                # Convert to native Python types
                value = row[i]
                row_dict[col_name] = value
            rows.append(row_dict)

        return {
            "sql": sql,
            "row_count": len(rows),
            "columns": column_names,
            "rows": rows[:100],  # Limit to 100 rows for display
            "note": "Limited to 100 rows" if len(rows) > 100 else None
        }
    except Exception as e:
        return {"error": f"SQL execution failed: {str(e)}"}
    finally:
        conn.close()


def get_sample_queries() -> dict:
    """
    Get sample SQL queries for reference

    Returns:
        Dict with example queries for learning
    """
    return {
        "database": str(SILVER_DB),
        "queries": [
            {
                "category": "Player Stats",
                "description": "Top 10 run scorers (all time)",
                "sql": """
SELECT
    p.name,
    COUNT(DISTINCT b.match_id) as matches,
    SUM(b.runs) as total_runs,
    ROUND(AVG(b.runs), 2) as avg_runs,
    MAX(b.runs) as high_score
FROM batting b
JOIN players p ON b.player_id = p.player_id
WHERE b.runs IS NOT NULL
GROUP BY p.name
HAVING COUNT(DISTINCT b.match_id) >= 20
ORDER BY total_runs DESC
LIMIT 10
                """.strip()
            },
            {
                "category": "Matches",
                "description": "Recent matches",
                "sql": """
SELECT
    start_date,
    team1,
    team2,
    winner,
    stadium,
    country
FROM matches
ORDER BY start_date DESC
LIMIT 10
                """.strip()
            },
            {
                "category": "Player Stats",
                "description": "Player career stats (example: find player_id first)",
                "sql": """
-- First, find player ID
SELECT player_id, name FROM players WHERE name LIKE '%Kohli%' LIMIT 5;

-- Then get stats for that player
SELECT
    p.name,
    COUNT(DISTINCT b.match_id) as matches,
    SUM(b.runs) as total_runs,
    ROUND(AVG(b.runs), 2) as average,
    MAX(b.runs) as highest_score,
    SUM(CASE WHEN b.runs >= 100 THEN 1 ELSE 0 END) as centuries,
    SUM(CASE WHEN b.runs >= 50 AND b.runs < 100 THEN 1 ELSE 0 END) as fifties
FROM batting b
JOIN players p ON b.player_id = p.player_id
WHERE b.player_id = 253802
GROUP BY p.name
                """.strip()
            },
            {
                "category": "Partnerships",
                "description": "Best partnerships at a venue",
                "sql": """
SELECT
    m.stadium,
    p1.name as player1,
    p2.name as player2,
    part.runs,
    part.balls,
    m.start_date
FROM partnerships part
JOIN matches m ON part.match_id = m.match_id
JOIN players p1 ON part.player1_id = p1.player_id
JOIN players p2 ON part.player2_id = p2.player_id
WHERE m.stadium = 'Melbourne Cricket Ground'
ORDER BY part.runs DESC
LIMIT 10
                """.strip()
            },
            {
                "category": "Head to Head",
                "description": "India vs Australia head-to-head",
                "sql": """
SELECT
    winner,
    COUNT(*) as wins
FROM matches
WHERE (team1 = 'India' AND team2 = 'Australia')
   OR (team1 = 'Australia' AND team2 = 'India')
GROUP BY winner
ORDER BY wins DESC
                """.strip()
            }
        ],
        "tips": [
            "Use get_database_schema to see available tables and columns",
            "Join players table to get names from player_id",
            "Join matches table to get venue, date, and team info",
            "batting and bowling tables have match-level performance data",
            "partnerships table has partnership details with player IDs"
        ]
    }
