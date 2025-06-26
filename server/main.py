"""PRIMCS MCP server entry-point.

Run with:
    python -m server.main

Starts an MCP stdio server exposing the `run_code` tool.
"""
from __future__ import annotations

import logging
import os

from fastmcp import FastMCP

from server.tools import run_code as run_code_tool

logger = logging.getLogger(__name__)

# Expose a globally named `mcp` so the FastMCP CLI can auto-discover it.
mcp = FastMCP(name="primcs", version="0.1.0")
run_code_tool.register(mcp)

if __name__ == "__main__":  # pragma: no cover
    port = int(os.getenv("PORT", "9000"))
    # Start the server with HTTP transport (modern replacement for SSE)
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port) 