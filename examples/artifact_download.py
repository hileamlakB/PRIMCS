import asyncio
import json

import aiohttp
from fastmcp import Client


async def main():
    # Step 1: Run code that generates an artifact (a PNG file)
    code = """
import matplotlib.pyplot as plt
plt.plot([1,2,3], [4,5,6])
plt.title('Test Plot')
plt.savefig('output/plot.png')
print('Plot saved!')
"""
    async with Client("http://localhost:9000/mcp") as client:
        # Call the run_code tool
        params = {
            "code": code,
            "requirements": ["matplotlib"],  # install matplotlib so the plot code runs
        }
        result = await client.call_tool("run_code", params)
        print("Result:", result)
        # Parse the result
        data = json.loads(result[0].text)
        artifacts = data.get("artifacts", [])
        if not artifacts:
            print("No artifacts returned!")
            return
        artifact = artifacts[0]
        rel_path = artifact["relative_path"]  # e.g. "plots/plot.png"
        print(f"Artifact relative path: {rel_path}")

        # Session ID is included in the tool response
        session_id = data.get("session_id")
        if not session_id:
            print("No session_id returned – cannot download artifact.")
            return

        # Step 2: Download the artifact using aiohttp with the required header
        artifact_url = f"http://localhost:9000/artifacts/{rel_path}"
        headers = {"mcp-session-id": session_id}
        print(
            f"Downloading artifact from: {artifact_url} with session_id: {session_id}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(artifact_url, headers=headers) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    from pathlib import Path
                    with Path("downloaded_plot.png").open("wb") as f:
                        f.write(content)
                    print("Artifact downloaded as downloaded_plot.png")
                else:
                    print(f"Failed to download artifact: {resp.status}")


if __name__ == "__main__":
    asyncio.run(main())
