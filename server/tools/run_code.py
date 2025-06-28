"""MCP tool: execute Python code in a sandbox."""
from typing import Any

from fastmcp import FastMCP

from server.sandbox.runner import run_code as sandbox_execute


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
            "Return values are captured from stdout/stderr, so be sure to `print()` anything you want back. "
            "Optional parameters:"\
            " • `requirements` – a list of pip specs to install before execution."\
            " • `files` – list of {url, mountPath?}. Each file is downloaded before execution and"\
            "   made available at ./mounts/<mountPath|filename>. Use that path in your code, e.g."\
            "   `pd.read_csv('mounts/my_data.csv')`. Files are read-only and disappear after the "\
            "   run."
        ),
    )
    async def _run_code(
        code: str,
        requirements: list[str] | None = None,
        files: list[dict[str, str]] | None = None,
        ctx: Any | None = None,
    ) -> dict[str, Any]:
        """Tool implementation compatible with FastMCP."""

        # Default mutable params
        requirements = requirements or []
        files = files or []

        if len(code) > 20_000:
            raise ValueError("Code block too large (20k char limit)")

        try:
            return await sandbox_execute(
                code=code,
                requirements=requirements,
                files=files,
                run_id=(ctx.request_id if ctx else "local"),
                logger=(ctx.logger if ctx else None),
            )
        except Exception as exc:  # noqa: BLE001
            # FastMCP automatically converts exceptions into ToolError responses.
            raise exc 