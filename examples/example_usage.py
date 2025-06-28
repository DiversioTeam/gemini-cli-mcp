"""Example usage of Gemini MCP tools."""

import asyncio

from gemini_mcp.tools import GeminiTools


async def main():
    """Demonstrate usage of Gemini MCP tools."""
    tools = GeminiTools()

    # Example 1: Simple prompt
    print("Example 1: Simple prompt")
    result = await tools.call_tool(
        "gemini_prompt", {"prompt": "What are the benefits of using MCP for AI integrations?"}
    )
    print(f"Response: {result}\n")

    # Example 2: Research a topic
    print("Example 2: Research a topic")
    result = await tools.call_tool(
        "gemini_research", {"topic": "Model Context Protocol (MCP) architecture and use cases"}
    )
    print(f"Research results: {result[:200]}...\n")

    # Example 3: Summarize content
    print("Example 3: Summarize content")
    result = await tools.call_tool(
        "gemini_summarize",
        {
            "content": "The Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to LLMs. It enables seamless integration between AI assistants and external tools, allowing them to access files, run commands, and interact with various services. MCP servers expose tools and resources that AI assistants can use to help users with tasks.",
            "summary_type": "bullet_points",
        },
    )
    print(f"Summary: {result}\n")


if __name__ == "__main__":
    asyncio.run(main())
