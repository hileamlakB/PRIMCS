<p align="left">
  <img src="primslogo.png" alt="PRIMS Logo" width="200"/>
</p>

# PRIMS – Python Runtime Interpreter MCP Server

PRIMS is a tiny open-source **Model Context Protocol (MCP)** server that lets LLM agents run arbitrary Python code in a secure, throw-away sandbox.

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


## Examples

### List available tools

You can use the provided script to list all tools exposed by the server:

```bash
python examples/list_tools.py
```

Expected output (tool names and descriptions may vary):

```
Available tools:
- run_code: Execute Python code in a secure sandbox with optional dependencies & file mounts.
- list_dir: List files/directories in your session workspace.
- preview_file: Preview up to 8 KB of a text file from your session workspace.
- persist_artifact: Upload an output/ file to a presigned URL for permanent storage.
```

### Run code via the MCP server

```bash
python examples/run_code.py
```

### Inspect your session workspace

```bash
python examples/inspect_workspace.py
```

This shows how to use the **`list_dir`** and **`preview_file`** tools to browse files your code created.

### Persist an artifact to permanent storage

The **`persist_artifact`** tool uploads a file from your `output/` directory to a presigned URL.

Example (Python):

```python
await client.call_tool("persist_artifact", {
    "relative_path": "plots/plot.png",
    "presigned_url": "https://bucket.s3.amazonaws.com/...signature...",
})
```

### Download an artifact

Small artifacts can be fetched directly:

```bash
curl -H "mcp-session-id: <your-session-id>" \
     http://localhost:9000/artifacts/plots/plot.png -o plot.png
```

---

## Available tools

| Tool                | Purpose |
|---------------------|---------------------------------------------------------------|
| `run_code`          | Execute Python in an isolated sandbox with optional pip deps. |
| `list_dir`          | List files/directories inside your session workspace.        |
| `preview_file`      | Return up to 8 KB of a text file for quick inspection.        |
| `persist_artifact`  | Upload an `output/` file to a client-provided presigned URL. |

See the `examples/` directory for end-to-end demos.

---

## Roadmap
- Speed up venv creation, use cached venvs
- Strict sandboxing (prevent accesing files beyond the venv folder, use user groups, firecrack vm)
- Harden CPU / memory limits 
- Artifact storage backend (S3, local disk)
- Unit tests & CI (GitHub Actions)
- Dependency resolution recommendations via **LLM sampling**
- Automated code debugging & error-fix suggestions via **LLM sampling**
- Auth and security
- OAuth 2.0 support for remote deployments
- Health-check and metrics endpoint for orchestration


PRs welcome!  See `LICENSE` (MIT). 
