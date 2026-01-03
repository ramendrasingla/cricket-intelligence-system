"""
MCP Server and Cricket Intelligence Tools

Atomic tools for cricket statistics and news, exposed via MCP protocol.
"""

from cricket_intelligence.api.tools.stats_tools import (
    get_database_schema,
    execute_sql,
    get_sample_queries,
)
from cricket_intelligence.api.tools.news_tools import (
    search_chromadb,
    query_cricket_articles,
)

__all__ = [
    # Stats tools
    "get_database_schema",
    "execute_sql",
    "get_sample_queries",
    # News tools
    "search_chromadb",
    "query_cricket_articles",
]
