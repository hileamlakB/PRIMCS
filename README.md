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

## Roadmap
- Speed up venv creation, use cached venvs
- Strict sandboxing (prevent accesing files beyond the venv folder, use user groups)
- Harden CPU / memory limits 
- Artifact storage backend (S3, local disk)
- Unit tests & CI (GitHub Actions)
- Dependency resolution recommendations via **LLM sampling**
- Automated code debugging & error-fix suggestions via **LLM sampling**
- Auth and security
- OAuth 2.0 support for remote deployments
- Health-check and metrics endpoint for orchestration


PRs welcome!  See `LICENSE` (MIT). 
