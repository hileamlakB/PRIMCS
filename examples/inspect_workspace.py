import asyncio
import json

from fastmcp import Client

SERVER_URL = "http://localhost:9000/mcp"


async def main() -> None:
    """Demonstrate workspace inspection tools."""
    async with Client(SERVER_URL) as client:
        # 1. Create a small text file via run_code
        code = (
            "with open('output/hello.txt', 'w') as f:\n"
            "    f.write('Hello inspection!\\nThis is a test file.')\n"
        )
        await client.call_tool("run_code", {"code": code})

        def parse_dir_response(resp):
            """Convert streamed TextContents into a list of DirEntry dicts, handling both list and single-entry payloads."""
            entries = []
            for msg in resp:
                obj = json.loads(msg.text)
                if isinstance(obj, list):
                    entries.extend(obj)
                else:
                    entries.append(obj)
            return entries

        # 2. List root of session workspace
        root_resp = await client.call_tool("list_dir", {})
        root_listing = parse_dir_response(root_resp)
        print("\n=== Workspace root ===")
        for entry in root_listing:
            print(f"{entry['type']:9} {entry['path']}")

        # 3. List contents of output/
        out_resp = await client.call_tool("list_dir", {"dir_path": "output"})
        out_listing = parse_dir_response(out_resp)
        print("\n=== output/ ===")
        for entry in out_listing:
            print(f"{entry['type']:9} {entry['path']}  {entry['size']} bytes")

        # 4. Preview the text file we just created
        preview_resp = await client.call_tool(
            "preview_file", {"relative_path": "output/hello.txt"}
        )
        preview = json.loads(preview_resp[0].text)
        print("\n=== Preview of output/hello.txt ===")
        print(preview["content"])


if __name__ == "__main__":
    asyncio.run(main())
