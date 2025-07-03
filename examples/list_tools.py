import asyncio
import json

from fastmcp import Client


async def main():
    async with Client("http://localhost:9000/mcp") as client:
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
            print(json.dumps(tool.inputSchema, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
