import asyncio
import json

from fastmcp import Client

SERVER_URL = "http://localhost:9000/mcp"


a_sync_code_first = """
import pandas as pd
# Dataset was downloaded via `files` parameter.
df = pd.read_csv('mounts/countries.csv')
print("First 5 rows:\\n", df.head())
"""

code_second = """
import pandas as pd
df = pd.read_csv('mounts/countries.csv')
print("Row count:", len(df))
"""


async def main() -> None:
    """Demonstrate that files persist for the lifetime of an MCP session."""
    async with Client("http://localhost:9000/mcp") as client:

        # 1. Run code that downloads a CSV file into the workspace mounts directory.
        first_params = {
            "code": a_sync_code_first,
            "files": [
                {
                    "url": "https://raw.githubusercontent.com/cs109/2014_data/master/countries.csv",
                    "mountPath": "countries.csv",
                }
            ],
        }
        run1 = await client.call_tool("run_code", first_params)
        data1 = json.loads(run1[0].text)
        print("\n=== Run #1 ===")
        print("STDOUT:\n", data1.get("stdout"))
        print("STDERR:\n", data1.get("stderr"))
        print("ARTIFACTS:", data1.get("artifacts"))

        # 2. Execute a second snippet in the SAME client session.
        #    We do NOT pass the `files` parameter again. The CSV should still exist.
        run2 = await client.call_tool("run_code", {"code": code_second})
        data2 = json.loads(run2[0].text)
        print("\n=== Run #2 ===")
        print("STDOUT:\n", data2.get("stdout"))
        print("STDERR:\n", data2.get("stderr"))
        print("ARTIFACTS:", data2.get("artifacts"))


if __name__ == "__main__":
    asyncio.run(main())
