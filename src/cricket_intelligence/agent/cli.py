#!/usr/bin/env python3
"""
Cricket Intelligence Agent - Simple CLI

Minimal CLI interface for cricket intelligence queries.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agent.cricket_agent import CricketAgent


async def main():
    """Simple interactive chat"""
    print("\n🏏 Cricket Intelligence Agent\n")

    # Check API key
    if not os.getenv("OPENAI_API"):
        print("❌ Error: OPENAI_API not found in .env file")
        sys.exit(1)

    # Initialize agent
    agent = CricketAgent()
    await agent.initialize()

    print("Ready! Ask me anything about cricket stats or news.")
    print("Type 'quit' to exit.\n")

    while True:
        # Get input
        try:
            query = input("\n🏏 You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not query or query.lower() in ['quit', 'exit']:
            break

        # Get response
        try:
            result = await agent.chat(query)
            print(f"\n🤖 Agent: {result['response']}")

            # Show insights
            insight = result.get("insight", {})
            if insight.get("insights"):
                print("\n📌 Key Insights:")
                for i, ins in enumerate(insight["insights"], 1):
                    print(f"   {i}. {ins}")

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

    # Cleanup
    await agent.close()
    print("\nGoodbye! 👋\n")


if __name__ == "__main__":
    asyncio.run(main())
