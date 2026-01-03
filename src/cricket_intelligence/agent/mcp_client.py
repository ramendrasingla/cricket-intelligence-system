"""
MCP Client Manager

Handles connection to MCP server and converts MCP tools to LangChain tools.
"""

import os
import sys
import json
from pathlib import Path
from typing import Any, Callable

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class MCPClientManager:
    """Manages MCP server connection and tool conversion"""

    def __init__(self, server_script_path: str):
        """
        Initialize MCP client manager

        Args:
            server_script_path: Path to MCP server script
        """
        self.server_script = server_script_path
        self.session = None
        self.read_stream = None
        self.write_stream = None
        self.langchain_tools = []
        self.client_context = None

    async def initialize(self) -> None:
        """Initialize connection to MCP server"""
        # Server parameters
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[self.server_script],
            env={**os.environ}
        )

        # Connect to server using async context manager
        self.client_context = stdio_client(server_params)
        self.read_stream, self.write_stream = await self.client_context.__aenter__()

        # Create and enter session context
        self.session = ClientSession(self.read_stream, self.write_stream)
        await self.session.__aenter__()

        # Initialize session
        await self.session.initialize()

        # Get tools and convert to LangChain
        tools_list = await self.session.list_tools()
        self.langchain_tools = self._convert_to_langchain_tools(tools_list.tools)

        print(f"✓ Connected to MCP server with {len(self.langchain_tools)} tools")

    def _convert_to_langchain_tools(self, mcp_tools: list) -> list[StructuredTool]:
        """
        Convert MCP tools to LangChain StructuredTool

        Args:
            mcp_tools: List of MCP tools

        Returns:
            List of LangChain StructuredTool
        """
        langchain_tools = []

        for mcp_tool in mcp_tools:
            # Create async wrapper - use default arg to capture tool_name properly
            async def tool_func(_tool_name=mcp_tool.name, **kwargs) -> str:
                """Tool function that calls MCP"""
                result = await self.session.call_tool(_tool_name, arguments=kwargs)

                # Extract text from MCP result
                if result.content and len(result.content) > 0:
                    return result.content[0].text
                return "{}"

            # Create input schema from MCP schema
            input_schema = self._create_pydantic_model(
                mcp_tool.name,
                mcp_tool.inputSchema
            )

            # Create LangChain tool
            lc_tool = StructuredTool.from_function(
                coroutine=tool_func,
                name=mcp_tool.name,
                description=mcp_tool.description or "",
                args_schema=input_schema,
                return_direct=False
            )

            langchain_tools.append(lc_tool)

        return langchain_tools

    def _create_pydantic_model(self, tool_name: str, json_schema: dict) -> type[BaseModel]:
        """
        Create Pydantic model from JSON schema

        Args:
            tool_name: Name of the tool
            json_schema: JSON schema from MCP tool

        Returns:
            Pydantic BaseModel class
        """
        # Extract properties and required fields
        properties = json_schema.get("properties", {})
        required = json_schema.get("required", [])

        # Build field definitions
        fields = {}
        for field_name, field_info in properties.items():
            field_type = self._json_type_to_python(field_info.get("type", "string"))
            field_description = field_info.get("description", "")
            field_default = ... if field_name in required else None

            fields[field_name] = (
                field_type,
                Field(default=field_default, description=field_description)
            )

        # Create dynamic Pydantic model
        model_name = f"{tool_name.replace('_', ' ').title().replace(' ', '')}Input"
        return type(model_name, (BaseModel,), {"__annotations__": {k: v[0] for k, v in fields.items()}, **{k: v[1] for k, v in fields.items()}})

    def _json_type_to_python(self, json_type: str) -> type:
        """Convert JSON schema type to Python type"""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        return type_mapping.get(json_type, str)

    def get_tools(self) -> list[StructuredTool]:
        """Get LangChain tools"""
        return self.langchain_tools

    async def close(self) -> None:
        """Close MCP connection"""
        if self.session:
            await self.session.__aexit__(None, None, None)
        if self.client_context:
            await self.client_context.__aexit__(None, None, None)
