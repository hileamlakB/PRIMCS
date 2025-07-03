"""MCP tool: persist an artifact to a client-provided presigned URL."""

from pathlib import Path

import aiohttp
from fastmcp import Context, FastMCP

from server.config import TMP_DIR

MAX_UPLOAD_BYTES = 1024 * 1024 * 20  # 20 MB cap for safety


def register(mcp: FastMCP) -> None:
    """Register the `persist_artifact` tool on a FastMCP server instance."""

    @mcp.tool(
        name="persist_artifact",
        description=(
            "Upload a file previously created by run_code to a presigned URL. "
            "The file path must be relative to the output/ directory of the current session, "
            "for example 'reports/report.pdf'. The client must include the same mcp-session-id "
            "header used for run_code so the tool can locate the correct session workspace."
        ),
    )
    async def _persist_artifact(
        relative_path: str,
        presigned_url: str,
        ctx: Context | None = None,
    ) -> dict:  # {uploaded_bytes: int, status: int}
        """Upload *relative_path* to *presigned_url* and return upload stats."""

        # Basic sanitisation
        if Path(relative_path).is_absolute() or ".." in Path(relative_path).parts:
            raise ValueError(
                "relative_path must be inside output/ and cannot contain '..'"
            )

        # Determine session ID
        sid = ctx.session_id
        if not sid and ctx.request_context.request:
            sid = ctx.request_context.request.headers.get("mcp-session-id")
        if not sid:
            raise ValueError("Missing session_id; ensure mcp-session-id header is set.")

        output_dir = TMP_DIR / f"session_{sid}" / "output"
        file_path = output_dir / relative_path
        if not file_path.is_file():
            raise FileNotFoundError("Artifact not found: " + relative_path)

        size = file_path.stat().st_size
        if size > MAX_UPLOAD_BYTES:
            raise ValueError(f"Artifact exceeds size limit ({MAX_UPLOAD_BYTES} bytes)")

        async with aiohttp.ClientSession() as session:
            with file_path.open("rb") as fh:
                resp = await session.put(presigned_url, data=fh)
                status = resp.status
                await resp.release()
                if status >= 400:
                    raise RuntimeError(f"Upload failed with HTTP {status}")

        return {"uploaded_bytes": size, "status": status}
