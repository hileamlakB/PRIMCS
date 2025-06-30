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
            "Execute Python code in a secure, throw-away sandbox. "
            "The sandbox is STATELESS: every call starts in a fresh env and any files you create are deleted afterwards. "
            "***YOU MUST use `print()` (or log to stderr) if you want the result returned.*** "
            "Optional parameters:"\
            " • `requirements` – a list of pip specs to install before execution."\
            " • `files` – list of {url, mountPath}. Each file is downloaded before execution and"\
            "   made available at ./mounts/<mountPath>. **mountPath is REQUIRED.** Use that path in your code, e.g."\
            "   `pd.read_csv('mounts/my_data.csv')`. Files are read-only and disappear after the "\
            "   run."
            " ***Example:*** `df.head()` **will NOT be returned**; you must call `print(df.head())` instead."
        ),
    )
    async def _run_code(
        code: str,
        requirements: list[str] | None = None,
        files: list[dict[str, str]] | None = None,
        ctx: Context | None = None,
    ) -> RunCodeResult:
        """Tool implementation compatible with FastMCP."""

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
            return await sandbox_execute(
                code=code,
                requirements=requirements,
                files=files,
                run_id=(ctx.request_id if ctx else "local"),
                session_id=sid,
                logger=None,
            )
        except Exception as exc:  # noqa: BLE001
            # FastMCP automatically converts exceptions into ToolError responses.
            raise exc 