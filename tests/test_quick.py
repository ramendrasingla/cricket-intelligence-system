#!/usr/bin/env python3
"""
Quick test to verify MCP connection works
"""

import os
import sys
import asyncio
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()


async def main():
    print("\n🏏 Quick MCP Connection Test\n")

    # Check API key
    if not os.getenv("OPENAI_API"):
        print("❌ OPENAI_API not found")
        return

    print("✓ API key found")

    # Import and create agent
    from agent.mcp_client import MCPClientManager

    server_script = str(PROJECT_ROOT / "api" / "mcp_server.py")
    print(f"✓ Server script: {server_script}")

    # Create MCP client
    client = MCPClientManager(server_script)
    print("✓ MCP client created")

    # Initialize
    print("\nInitializing MCP connection...")
    await client.initialize()

    # Get tools
    tools = client.get_tools()
    print(f"\n✓ Got {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool.name}")

    # Close
    await client.close()
    print("\n✓ Connection closed\n")
    print("✅ All checks passed!\n")


if __name__ == "__main__":
    asyncio.run(main())
