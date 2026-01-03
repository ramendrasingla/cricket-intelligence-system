"""
Output Data Schemas

Pydantic models for structured outputs from cricket intelligence agent.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class SQLQueryResult(BaseModel):
    """Result from SQL query execution"""
    query: str = Field(description="The SQL query that was executed")
    reasoning: str = Field(description="Brief explanation of how this SQL was constructed")
    row_count: int = Field(description="Number of rows returned")
    columns: list[str] = Field(description="Column names in the result")
    rows: list[dict] = Field(description="Query result rows")
    success: bool = Field(default=True, description="Whether query executed successfully")
    error: Optional[str] = Field(default=None, description="Error if query failed")


class NewsArticle(BaseModel):
    """Individual news article"""
    title: str = Field(description="Article title")
    description: str = Field(description="Article description")
    url: str = Field(description="Article URL")
    source: str = Field(description="News source")
    published_at: str = Field(description="Publication date")


class NewsSearchResult(BaseModel):
    """Result from news search"""
    query: str = Field(description="The search query")
    reasoning: str = Field(description="Brief explanation of search approach")
    results_count: int = Field(description="Number of articles found")
    articles: list[NewsArticle] = Field(description="List of articles")
    used_fresh_api: bool = Field(
        default=False,
        description="Whether fresh news was fetched via GNews API"
    )


class CricketInsight(BaseModel):
    """Final cricket intelligence output with insights"""
    query_type: Literal["stats", "news", "mixed"] = Field(
        description="Type of query processed"
    )
    user_query: str = Field(description="Original user query")
    reasoning: str = Field(description="Brief explanation of how we arrived at this answer")
    insights: list[str] = Field(description="Key findings extracted from data")
    summary: str = Field(description="Natural language summary")
    raw_data: dict = Field(description="Raw structured data from tools")
    confidence: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Confidence level in the answer"
    )


class ToolExecutionResult(BaseModel):
    """Result from a tool execution"""
    tool_name: str = Field(description="Name of the tool executed")
    success: bool = Field(description="Whether execution was successful")
    data: dict = Field(description="Result data from tool")
    error: Optional[str] = Field(default=None, description="Error message if failed")
