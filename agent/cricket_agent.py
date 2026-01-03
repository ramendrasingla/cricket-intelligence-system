"""
Cricket Intelligence Agent

Main LangGraph agent that orchestrates MCP tools for cricket intelligence.
"""

import os
import sys
from pathlib import Path
from typing import Literal, Annotated
from operator import add

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

from agent.mcp_client import MCPClientManager
from agent.insight_generator import InsightGenerator
from agent.schemas import CricketInsight

# Load environment
load_dotenv()


# ===== Agent State =====

class CricketAgentState(MessagesState):
    """State for cricket intelligence agent"""
    tool_results: Annotated[list[dict], add] = []  # Accumulate tool results
    final_insight: dict = {}  # Final insight with summary


# ===== Cricket Agent =====

class CricketAgent:
    """Cricket Intelligence Agent with MCP integration"""

    def __init__(self):
        self.mcp_client = None
        self.llm = None
        self.insight_generator = None
        self.agent = None
        self.tools = []

    async def initialize(self):
        """Initialize MCP connection and build LangGraph"""
        print("\n🏏 Initializing Cricket Intelligence Agent...")

        # Initialize MCP client
        project_root = Path(__file__).parent.parent
        server_script = str(project_root / "api" / "mcp_server.py")

        self.mcp_client = MCPClientManager(server_script)
        await self.mcp_client.initialize()

        self.tools = self.mcp_client.get_tools()

        # Initialize LLM
        api_key = os.getenv("OPENAI_API")
        if not api_key:
            raise ValueError("OPENAI_API not found in environment")

        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=api_key
        )

        # Initialize insight generator
        self.insight_generator = InsightGenerator(self.llm)

        # Build LangGraph
        self._build_graph()

        print("✓ Agent initialized and ready\n")

    def _build_graph(self):
        """Build the LangGraph workflow"""

        # Bind tools to LLM
        llm_with_tools = self.llm.bind_tools(self.tools)

        # System message
        system_message = SystemMessage(content="""You are a cricket intelligence assistant with access to both cricket statistics and news.

**Available Tools:**
1. **get_database_schema** - Get database structure (use FIRST before SQL queries)
2. **execute_sql** - Run SQL queries on cricket stats (Test cricket 1877-2024)
3. **get_sample_queries** - Get example SQL queries for reference
4. **search_chromadb** - Search cached cricket news articles (semantic search)
5. **query_cricket_articles** - Fetch fresh news from GNews API

**Query Strategy:**
- For statistics/records → Use SQL tools (get_database_schema → execute_sql)
- For news/articles → Use search_chromadb first, if empty use query_cricket_articles
- For player queries → Combine both: stats from SQL + recent news

**SQL Best Practices:**
- Always call get_database_schema first to understand tables
- JOIN with players table to get player names (don't use player_id directly)
- Use get_sample_queries if you need examples

**Important:**
- Explain your reasoning briefly before calling tools
- If a query fails, try a different approach
- Be concise but informative in responses
""")

        # Define agent node
        def agent_node(state: CricketAgentState):
            """Main agent reasoning node"""
            messages = [system_message] + state["messages"]
            response = llm_with_tools.invoke(messages)
            return {"messages": [response]}

        # Define tools node (wraps LangChain ToolNode)
        tool_node = ToolNode(self.tools)

        async def tools_node_wrapper(state: CricketAgentState):
            """Wrapper to capture tool results"""
            # Call tools asynchronously
            result = await tool_node.ainvoke(state)

            # Extract tool results from messages
            new_messages = result["messages"]
            tool_results = []

            for msg in new_messages:
                if isinstance(msg, ToolMessage):
                    tool_results.append({
                        "name": msg.name if hasattr(msg, 'name') else "unknown",
                        "content": msg.content
                    })

            return {
                "messages": new_messages,
                "tool_results": tool_results
            }

        # Define insight generator node
        async def insight_node(state: CricketAgentState):
            """Generate insights from tool results"""
            # Get the original user query
            user_query = ""
            for msg in state["messages"]:
                if isinstance(msg, HumanMessage):
                    user_query = msg.content
                    break

            # Determine query type based on tools used
            tool_names = [r.get("name", "") for r in state["tool_results"]]
            if any("sql" in name.lower() or "schema" in name.lower() or "sample" in name.lower() for name in tool_names):
                if any("chroma" in name.lower() or "article" in name.lower() for name in tool_names):
                    query_type = "mixed"
                else:
                    query_type = "stats"
            else:
                query_type = "news"

            # Generate insights
            insights_data = await self.insight_generator.generate_insights(
                query=user_query,
                tool_results=state["tool_results"],
                query_type=query_type
            )

            # Create final response message
            summary_msg = AIMessage(content=insights_data["summary"])

            return {
                "messages": [summary_msg],
                "final_insight": {
                    "user_query": user_query,
                    "query_type": query_type,
                    "insights": insights_data["insights"],
                    "summary": insights_data["summary"],
                    "confidence": insights_data["confidence"],
                    "raw_data": state["tool_results"]
                }
            }

        # Define conditional edges
        def should_continue(state: CricketAgentState) -> Literal["tools", "insights", "end"]:
            """Determine next step"""
            last_message = state["messages"][-1]

            # If LLM made tool calls, go to tools
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools"

            # If we have tool results, generate insights
            if state["tool_results"]:
                return "insights"

            # Otherwise end
            return "end"

        # Build graph
        workflow = StateGraph(CricketAgentState)

        # Add nodes
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tools_node_wrapper)
        workflow.add_node("insights", insight_node)

        # Add edges
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "insights": "insights",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")  # Loop back to agent after tools
        workflow.add_edge("insights", END)

        # Compile
        self.agent = workflow.compile()

    async def chat(self, user_input: str) -> dict:
        """
        Send a message and get response

        Args:
            user_input: User's question

        Returns:
            Dict with response and insights
        """
        # Invoke agent
        result = await self.agent.ainvoke({
            "messages": [HumanMessage(content=user_input)],
            "tool_results": [],
            "final_insight": {}
        })

        # Extract response
        final_message = result["messages"][-1]
        response_text = final_message.content if hasattr(final_message, 'content') else str(final_message)

        return {
            "response": response_text,
            "insight": result.get("final_insight", {}),
            "messages": result["messages"]
        }

    async def close(self):
        """Clean up resources"""
        if self.mcp_client:
            await self.mcp_client.close()
