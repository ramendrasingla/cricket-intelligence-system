#!/usr/bin/env python3
"""
Cricket Query MCP Server

MCP server that exposes atomic cricket data tools.
LLM orchestrates these tools for intelligent querying.

Architecture:
- cricket_news_tools.py: ChromaDB + GNews API tools
- cricket_stats_tools.py: DuckDB SQL tools
- mcp_server.py: MCP server definitions and routing

Tools:
- Cricket News: search_chromadb, query_cricket_articles
- Cricket Stats: get_database_schema, execute_sql, get_sample_queries

Usage:
    python api/mcp_server.py
"""

import json
import sys
from pathlib import Path
from dotenv import load_dotenv

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import tool implementations
from api.mcp_tools.cricket_news_tools import (
    search_chromadb,
    query_cricket_articles
)
from api.mcp_tools.cricket_stats_tools import (
    get_database_schema,
    execute_sql,
    get_sample_queries
)

# Load environment
load_dotenv()

# Initialize MCP server
app = Server("cricket-query-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Define all available MCP tools"""
    return [
        # ===== Cricket News Tools =====
        Tool(
            name="search_chromadb",
            description=(
                "Search cricket news in ChromaDB using semantic similarity. "
                "Returns relevant articles based on meaning, not just keywords. "
                "If no results found, use query_cricket_articles to get fresh news."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'Kohli century', 'India Australia Test match')"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["query"]
            }
        ),

        Tool(
            name="query_cricket_articles",
            description=(
                "Fetch fresh cricket news from GNews API and automatically ingest to ChromaDB. "
                "Use when search_chromadb returns no results. "
                "After calling this, call search_chromadb again to get the new articles."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for GNews API"
                    },
                    "max_articles": {
                        "type": "integer",
                        "description": "Max articles to fetch (default: 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["query"]
            }
        ),

        # ===== Cricket Stats Tools =====
        Tool(
            name="get_database_schema",
            description=(
                "Get cricket database schema information. "
                "Returns table structures, columns, types, and row counts. "
                "ALWAYS use this BEFORE generating SQL queries to understand available data."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": (
                            "Optional: specific table name to get schema for. "
                            "Options: players, matches, batting, bowling, fall_of_wickets, partnerships. "
                            "Omit to get all tables."
                        )
                    }
                }
            }
        ),

        Tool(
            name="execute_sql",
            description=(
                "Execute SQL query on cricket database (Test cricket 1877-2024). "
                "Returns query results. Read-only, SELECT queries only. "
                "Use get_database_schema first to see available tables and columns."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query to execute (SELECT only, no DML/DDL)"
                    }
                },
                "required": ["sql"]
            }
        ),

        Tool(
            name="get_sample_queries",
            description=(
                "Get example SQL queries for reference. "
                "Useful for learning database structure and query patterns. "
                "Shows common use cases like top scorers, player stats, head-to-head."
            ),
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Route tool calls to appropriate implementation"""

    try:
        # Cricket News Tools
        if name == "search_chromadb":
            result = search_chromadb(
                query=arguments["query"],
                top_k=arguments.get("top_k", 5)
            )

        elif name == "query_cricket_articles":
            result = query_cricket_articles(
                query=arguments["query"],
                max_articles=arguments.get("max_articles", 5)
            )

        # Cricket Stats Tools
        elif name == "get_database_schema":
            result = get_database_schema(
                table_name=arguments.get("table_name")
            )

        elif name == "execute_sql":
            result = execute_sql(sql=arguments["sql"])

        elif name == "get_sample_queries":
            result = get_sample_queries()

        else:
            result = {"error": f"Unknown tool: {name}"}

        # Return JSON response
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    except Exception as e:
        error_result = {
            "error": f"Tool execution failed: {str(e)}",
            "tool": name,
            "arguments": arguments
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def main():
    """Run the MCP server via stdio"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
