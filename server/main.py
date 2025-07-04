"""PRIMCS MCP server entry-point.

Run with:
    python -m server.main

Starts an MCP stdio server exposing the `run_code` tool.
"""

import logging
import os
from pathlib import Path

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import FileResponse, Response

from server.config import TMP_DIR
from server.prompts import python_programmer as python_programmer_prompt
from server.tools import mount_file as mount_file_tool
from server.tools import persist_artifact as persist_artifact_tool
from server.tools import run_code as run_code_tool
from server.tools import workspace_inspect as workspace_inspect_tool

logger = logging.getLogger(__name__)

# Expose a globally named `mcp` so the FastMCP CLI can auto-discover it.
mcp = FastMCP(name="primcs", version="0.1.0")
run_code_tool.register(mcp)
persist_artifact_tool.register(mcp)
workspace_inspect_tool.register(mcp)
mount_file_tool.register(mcp)
python_programmer_prompt.register(mcp)


@mcp.custom_route("/artifacts/{relative_path:path}", methods=["GET"])
async def get_artifact(request: Request) -> Response:
    """
    Serve an artifact file for the current session. The client must include
    the session ID in the "mcp-session-id" header. The URL path is the
    relative path returned by the tool (e.g. "plots/plot.png"), which is
    resolved under session_<id>/output/.
    """
    relative_path = request.path_params["relative_path"]
    relative_path = os.path.normpath(relative_path)
    path_obj = Path(relative_path)
    if relative_path.startswith("..") or path_obj.is_absolute():
        return Response("Invalid artifact path", status_code=400)

    session_id = request.headers.get("mcp-session-id")
    if not session_id:
        return Response("Missing mcp-session-id header", status_code=400)

    base_dir = TMP_DIR / f"session_{session_id}" / "output"
    file_path = base_dir / relative_path

    try:
        file_path = file_path.resolve(strict=True)
    except FileNotFoundError:
        return Response("File not found", status_code=404)

    # Ensure file is within the output directory
    if not str(file_path).startswith(str(base_dir.resolve())):
        return Response("Forbidden", status_code=403)
    if not file_path.is_file():
        return Response("Not a file", status_code=404)

    return FileResponse(str(file_path), filename=file_path.name)


if __name__ == "__main__":  # pragma: no cover
    port = int(os.getenv("PORT", "9000"))
    # Start the server with HTTP transport (modern replacement for SSE)
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
