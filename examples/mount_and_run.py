import asyncio
import json
from fastmcp import Client

SERVER = "http://localhost:9000/mcp"
CSV_URL = "https://raw.githubusercontent.com/cs109/2014_data/master/countries.csv"

async def main() -> None:
    async with Client(SERVER) as client:
        # 1. Mount the CSV once for this session
        mount_params = {
            "url": CSV_URL,
            "mount_path": "data/countries.csv",
        }
        mount_resp = await client.call_tool("mount_file", mount_params)
        print("Mount response:", mount_resp[0].text)

        # 2. Run code that reads the mounted CSV without passing `files`
        code = """
import pandas as pd
import os
path = 'mounts/data/countries.csv'
print('File exists:', os.path.exists(path))
print('Row count:', len(pd.read_csv(path)))
"""
        run_resp = await client.call_tool("run_code", {"code": code})
        print("Run result:")
        print(json.dumps(json.loads(run_resp[0].text), indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 