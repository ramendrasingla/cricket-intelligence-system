"""
Insight Generator

Converts structured tool results into natural language insights.
Extracts key findings and creates clear summaries.
"""

import json
from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class InsightGenerator:
    """Generates natural language insights from structured data"""

    def __init__(self, llm: ChatOpenAI):
        """
        Initialize insight generator

        Args:
            llm: LangChain LLM instance
        """
        self.llm = llm

    async def generate_insights(
        self,
        query: str,
        tool_results: list[dict],
        query_type: str
    ) -> dict:
        """
        Generate insights from tool execution results

        Args:
            query: Original user query
            tool_results: List of tool execution results
            query_type: Type of query ("stats", "news", or "mixed")

        Returns:
            Dict with insights and summary
        """
        # Build context from tool results
        context = self._build_context(tool_results)

        # System prompt for insight generation
        system_prompt = """You are a cricket intelligence analyst. Your job is to:

1. Extract key findings from data
2. Create clear, concise summaries
3. Add cricket context where relevant

Guidelines:
- Focus on the most important insights (top 3-5 findings)
- Use specific numbers and facts
- Explain what the numbers mean in cricket context
- Be concise but informative
- Avoid speculation - stick to the data

Output format:
{
  "insights": ["insight 1", "insight 2", ...],
  "summary": "A clear 2-3 sentence summary",
  "confidence": "high" | "medium" | "low"
}
"""

        # Create user prompt
        user_prompt = f"""User Query: {query}

Query Type: {query_type}

Tool Results:
{context}

Please analyze the data and provide key insights and a summary."""

        # Generate insights
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = await self.llm.ainvoke(messages)

        # Parse response
        try:
            result = json.loads(response.content)
            return {
                "insights": result.get("insights", []),
                "summary": result.get("summary", ""),
                "confidence": result.get("confidence", "medium")
            }
        except json.JSONDecodeError:
            # Fallback if LLM doesn't return valid JSON
            return {
                "insights": [response.content],
                "summary": response.content,
                "confidence": "low"
            }

    def _build_context(self, tool_results: list[dict]) -> str:
        """
        Build context string from tool results

        Args:
            tool_results: List of tool execution results

        Returns:
            Formatted context string
        """
        context_parts = []

        for i, result in enumerate(tool_results, 1):
            tool_name = result.get("name", "Unknown")
            content = result.get("content", "")

            # Try to parse content if it's JSON
            try:
                content_dict = json.loads(content) if isinstance(content, str) else content
                content_formatted = json.dumps(content_dict, indent=2)
            except:
                content_formatted = str(content)

            context_parts.append(f"Tool {i}: {tool_name}\n{content_formatted}")

        return "\n\n".join(context_parts)

    def extract_sql_reasoning(self, schema_info: dict, query: str) -> str:
        """
        Generate brief reasoning for SQL query construction

        Args:
            schema_info: Database schema information
            query: User's natural language query

        Returns:
            Reasoning string
        """
        # Simple template-based reasoning for now
        # In a full implementation, this could use LLM
        return f"Constructed SQL based on user query '{query}' using available schema"

    def extract_news_reasoning(self, search_query: str, has_cached: bool) -> str:
        """
        Generate brief reasoning for news search approach

        Args:
            search_query: Search query used
            has_cached: Whether cached results were found

        Returns:
            Reasoning string
        """
        if has_cached:
            return f"Searched ChromaDB for '{search_query}' and found cached results"
        else:
            return f"No cached results for '{search_query}', fetched fresh news from GNews API"
