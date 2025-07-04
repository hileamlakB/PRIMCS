"""MCP tool: download one or more remote files into mounts/ for the current session."""

from pathlib import Path

from fastmcp import Context, FastMCP

from server.config import TMP_DIR
from server.sandbox.downloader import download_files


def _session_root(ctx: Context | None) -> Path:
    sid: str | None = None
    if ctx:
        sid = ctx.session_id
        if not sid and ctx.request_context.request:
            sid = ctx.request_context.request.headers.get("mcp-session-id")
    if not sid:
        raise ValueError(
            "Missing session_id; include mcp-session-id header or create session-aware client."
        )
    root = TMP_DIR / f"session_{sid}"
    root.mkdir(parents=True, exist_ok=True)
    (root / "mounts").mkdir(parents=True, exist_ok=True)
    return root


def register(mcp: FastMCP) -> None:
    """Register the mount_file tool."""

    @mcp.tool(
        name="mount_file",
        description=(
            "Download a remote file once per session and store it under mounts/<mountPath>. "
            "Subsequent run_code calls can access it via that path without re-downloading."
        ),
    )
    async def _mount_file(
        url: str,
        mount_path: str,
        ctx: Context | None = None,
    ) -> dict:  # {"mounted_as": "mounts/data/my.csv", "bytes": N}
        if (
            Path(mount_path).is_absolute()
            or ".." in Path(mount_path).parts
            or not mount_path
        ):
            raise ValueError("mount_path must be a relative path without '..'")
        root = _session_root(ctx)
        mounts_dir = root / "mounts"
        spec: dict[str, str] = {"url": url, "mountPath": mount_path}
        downloaded: list[Path] = await download_files([spec], mounts_dir)
        local = downloaded[0]
        return {
            "mounted_as": str(local.relative_to(root)),
            "bytes": local.stat().st_size,
        }
