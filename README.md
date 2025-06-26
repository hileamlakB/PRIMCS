# PRIMCS – Python Runtime Interpreter MCP Server

PRIMCS is a tiny open-source **Model Context Protocol (MCP)** server that lets LLM agents run arbitrary Python code in a secure, throw-away sandbox.

•   **One tool, one job.**  Exposes a single MCP tool – `run_code` – that executes user-supplied Python and streams back `stdout / stderr`.
•   **Isolated & reproducible.**  Each call spins up a fresh virtual-env, installs any requested pip packages, mounts optional read-only files, then nukes the workspace.
•   **Zero config.**  Works over MCP/stdio or drop it in Docker.

---

## Quick-start

### 1. Local development environment

```bash
chmod +x scripts/setup_env.sh   # once, to make the script executable
./scripts/setup_env.sh          # creates .venv & installs deps

# activate the venv in each new shell
source .venv/bin/activate
```

### 2. Launch the server

```bash
fastmcp run server/main.py           # binds http://0.0.0.0:9000/mcp
```

### 3. Docker

```bash
# Quick one-liner (build + run)
chmod +x scripts/docker_run.sh
./scripts/docker_run.sh         # prints the MCP URL when ready
```

If you prefer the manual commands:

```bash
docker build -t primcs .
docker run -p 9000:9000 primcs
```

Connect from a client:

```bash
fastmcp dev server/main.py   # launches an inspector & auto-connects
# then call the `run_code` tool via UI
```

### Discover available tools (Python client)

```python
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:9000/mcp") as client:
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

asyncio.run(main())
```

## Examples

### List available tools

You can use the provided script to list all tools exposed by the server:

```bash
python examples/list_tools.py
```

Expected output:
```
Available tools:
- run_code: Execute Python code in a secure sandbox with optional dependencies & file mounts.
```

### Run code via the MCP server

You can execute Python code in the sandbox using the `run_code` tool:

```bash
python examples/run_code.py
```

Expected output:
```
Result:
{'stdout': 'Hello from FastMCP!\n', 'stderr': '', 'artifacts': []}
```

See the `examples/` directory for more advanced usage and client patterns.

---

## MCP Tool: `run_code`
Input schema (abridged):
```jsonc
{
  "code":        "<python-source>",
  "requirements": ["numpy>=1.26"],  // optional
  "files": [{ "url": "https://…", "mountPath": "data.csv" }] // optional
}
```

Output:
```jsonc
{ "stdout": "…", "stderr": "…", "artifacts": [] }
```

---

## Roadmap
- Speed up venv creation, use cached venvs
- Harden CPU / memory limits 
- Artifact storage backend (S3, local disk)
- Unit tests & CI (GitHub Actions)
- Dependency resolution recommendations via **LLM sampling**
- Automated code debugging & error-fix suggestions via **LLM sampling**
- Auth and security
- OAuth 2.0 support for remote deployments
- Health-check and metrics endpoint for orchestration


PRs welcome!  See `LICENSE` (MIT). 

fastmcp dev server/main.py   # launches an inspector & auto-connects
# then call the `run_code` tool via UI 