import asyncio

from fastmcp import Client


async def main():
    async with Client("http://localhost:9000/mcp") as client:
        code = "print('Hello from FastMCP!')"
        result = await client.call_tool("run_code", {"code": code})
        print("Result: \n\t", result)


if __name__ == "__main__":
    asyncio.run(main())
