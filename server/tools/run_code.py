"""MCP tool: execute Python code in a sandbox."""

from fastmcp import Context, FastMCP

from server.sandbox.runner import RunCodeResult
from server.sandbox.runner import run_code as sandbox_execute

RESPONSE_FEEDBACK = (
    "No output detected. Use print() (or log to stderr) to display results. "
    "For pandas DataFrames, call print(df.head()) instead of just df.head(). "
    "To see all columns or wider tables, run "
    "pd.set_option('display.max_columns', None) and "
    "pd.set_option('display.width', 10000) before printing. "
    "Ensure your code is a self-contained script (not notebook style) and "
    "reference mounted files "
    "with their mount path, e.g. pd.read_csv('mounts/my_data.csv'). "
    "If an error occurs, double-check these points first."
)


def register(mcp: FastMCP) -> None:
    """Register the `run_code` tool on a FastMCP server instance.

    Usage (inside server.main):

        from server.tools import run_code
        run_code.register(mcp)
    """

    @mcp.tool(
        name="run_code",
        description=(
            "Run self-contained Python scripts in an isolated sandbox. "
            "Send a 'session_id' header to reuse the environment across runs; "
            "otherwise the sandbox is reset each time. "
            "Use print() (or log to stderr) to capture output—expressions "
            "like df.head() alone will not be returned. "
            "Store any artifacts you want back in the output/ directory; they "
            "are returned as relative paths and downloadable via "
            "/artifacts/{relative_path}. "
            "Mounted files are available at mounts/<mountPath>. "
            "If stdout is empty or execution fails, a 'feedback' string is "
            "added to the response with suggestions. "
            "Tip: when printing large pandas DataFrames, call "
            "pd.set_option('display.max_columns', None) and "
            "pd.set_option('display.width', 10000) first. Moreover try to get "
            "column names separately."
            "Optional parameters: requirements (list of pip specs) and files "
            "[{url, mountPath}]. "
            "Each file is downloaded before execution and made available at "
            "./mounts/<mountPath>. "
        ),
    )
    async def _run_code(
        code: str,
        requirements: list[str] | None = None,
        files: list[dict[str, str]] | None = None,
        ctx: Context | None = None,
    ) -> RunCodeResult:
        """Tool implementation compatible with FastMCP.

        If a session_id is provided, the environment and files persist for the
        session. If not, the sandbox is stateless and files are deleted after
        each run. Artifacts are returned as relative paths and downloadable via
        /artifacts/{relative_path}. The session_id is always included in the
        response if available.

        If stdout is empty or an error occurs, a feedback array is included in
        the response with suggestions to use print statements and ensure code
        is self-contained.
        """

        # Default mutable params
        requirements = requirements or []
        files = files or []

        if len(code) > 20_000:
            raise ValueError("Code block too large (20k char limit)")

        sid = ctx.session_id  # may be None on Streamable-HTTP
        if not sid and ctx.request_context.request:
            # see issue https://github.com/modelcontextprotocol/python-sdk/
            # issues/1063 for more details
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
            # Add feedback if stdout is empty
            if not result.get("stdout"):
                result = dict(result)
                result["feedback"] = RESPONSE_FEEDBACK
            return result
        except Exception as exc:  # noqa: BLE001
            # FastMCP automatically converts exceptions into ToolError
            # responses.
            feedback = [
                (
                    "An error occurred. Please ensure your code is "
                    "self-contained, uses print statements for output, and is "
                    "not written in notebook style."
                )
            ]
            raise type(exc)(str(exc) + f"\nFEEDBACK: {feedback[0]}") from exc
