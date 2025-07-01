"""MCP tool: execute Python code in a sandbox."""
from typing import Any

from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_http_headers

from server.sandbox.runner import run_code as sandbox_execute, RunCodeResult


def register(mcp: FastMCP) -> None:
    """Register the `run_code` tool on a FastMCP server instance.

    Usage (inside server.main):

        from server.tools import run_code
        run_code.register(mcp)
    """

    @mcp.tool(
        name="run_code",
        description=(
            "Execute Python code in a secure sandbox. "
            "If a session_id is provided (via connection headers), the environment and files persist for the duration of the session. "
            "If no session_id is provided, the sandbox is stateless and files are deleted after each run. "
            "***YOU MUST use `print()` (or log to stderr) if you want the result returned.*** "
            " ***Example:*** `df.head()` **will NOT be returned**; you must call `print(df.head())` instead."
            "All output files you want to persist must be saved inside the output/ directory. "
            "Artifacts generated in the output/ directory are returned as relative paths (e.g. 'plots/plot.png'). "
            "You can download them via GET /artifacts/{relative_path}. "
            
            "Optional parameters:"
            " • `requirements` – a list of pip specs to install before execution."
            " • `files` – list of {url, mountPath}. Each file is downloaded before execution and"
            "   made available at ./mounts/<mountPath>. **mountPath is REQUIRED.** Use that path in your code, e.g."
            "   `pd.read_csv('mounts/my_data.csv')`. Files are read-only and disappear after the run."
        ),
    )
    async def _run_code(
        code: str,
        requirements: list[str] | None = None,
        files: list[dict[str, str]] | None = None,
        ctx: Context | None = None,
    ) -> RunCodeResult:
        """Tool implementation compatible with FastMCP. If a session_id is provided, the environment and files persist for the session. If not, the sandbox is stateless and files are deleted after each run. Artifacts are returned as relative paths and downloadable via /artifacts/{relative_path}. The session_id is always included in the response if available."""

        # Default mutable params
        requirements = requirements or []
        files = files or []

        if len(code) > 20_000:
            raise ValueError("Code block too large (20k char limit)")

        sid = ctx.session_id  # may be None on Streamable-HTTP
        if not sid and ctx.request_context.request:
            # see issue https://github.com/modelcontextprotocol/python-sdk/issues/1063 for more details
            sid = ctx.request_context.request.headers.get("mcp-session-id") 

        try:
            result = await sandbox_execute(
                code=code,
                requirements=requirements,
                files=files,
                run_id=(ctx.request_id if ctx else "local"),
                session_id=sid,
            )
            # Always include session_id in the response if available
            if sid:
                result = dict(result)
                result["session_id"] = sid
            return result
        except Exception as exc:  # noqa: BLE001
            # FastMCP automatically converts exceptions into ToolError responses.
            raise exc 