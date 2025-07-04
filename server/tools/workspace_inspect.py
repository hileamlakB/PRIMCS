# """Workspace inspection tools for session files."""

import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import aiofiles
from fastmcp import Context, FastMCP

from server.config import TMP_DIR

_MAX_PREVIEW_BYTES = 8 * 1024  # 8 KB


class DirEntry(TypedDict):
    name: str
    path: str
    type: str  # 'file' | 'directory'
    size: int
    modified: str  # ISO timestamp


class FilePreview(TypedDict):
    name: str
    path: str
    size: int
    mime: str
    content: str  # UTF-8 text (truncated)


def _get_session_root(ctx: Context | None) -> Path:
    sid: str | None = None
    if ctx:
        sid = ctx.session_id
        if not sid and ctx.request_context.request:
            sid = ctx.request_context.request.headers.get("mcp-session-id")
    if not sid:
        raise ValueError(
            "Missing session_id; ensure the client includes the mcp-session-id header or uses a session-aware context."
        )
    root = TMP_DIR / f"session_{sid}"
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def _resolve_in_session(ctx: Context | None, relative_path: str) -> Path:
    root = _get_session_root(ctx)
    # Normalise & forbid traversal
    rel = Path(os.path.normpath(relative_path)) if relative_path else Path()
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(
            "Path must be relative to session root and may not contain '..'."
        )
    resolved = (root / rel).resolve()
    if not str(resolved).startswith(str(root.resolve())):
        raise ValueError("Path escapes session workspace.")
    return resolved


def register(mcp: FastMCP) -> None:
    """Register workspace inspection tools on the given MCP server."""

    @mcp.tool(
        name="list_dir",
        description=(
            "List files and directories within the current session workspace. "
            "Parameter `path` is relative to the session root (default '.') and cannot contain '..'."
        ),
    )
    async def _list_dir(
        dir_path: str | None = None, ctx: Context | None = None
    ) -> list[DirEntry]:
        target = _resolve_in_session(ctx, dir_path or ".")
        if not target.is_dir():
            raise ValueError("Specified path is not a directory")
        entries: list[DirEntry] = []
        for p in sorted(target.iterdir(), key=lambda p: p.name):
            stat = p.stat()
            entries.append(
                {
                    "name": p.name,
                    "path": str(p.relative_to(_get_session_root(ctx))),
                    "type": "directory" if p.is_dir() else "file",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
            )
        return entries

    @mcp.tool(
        name="preview_file",
        description=(
            "Return up to 8 KB of a text file from the session workspace for quick inspection. "
            "`relative_path` must point to a file inside the session and not contain '..'."
        ),
    )
    async def _preview_file(
        relative_path: str, ctx: Context | None = None
    ) -> FilePreview:
        file_path = _resolve_in_session(ctx, relative_path)
        if not file_path.is_file():
            raise FileNotFoundError("File not found")
        size = file_path.stat().st_size
        if (
            size > _MAX_PREVIEW_BYTES * 4
        ):  # arbitrary limit 32 KB for previewable text files
            raise ValueError("File too large for preview")
        # Read up to _MAX_PREVIEW_BYTES and decode
        async with aiofiles.open(file_path, "rb") as fh:
            data = await fh.read(_MAX_PREVIEW_BYTES)
        try:
            content = data.decode("utf-8", errors="replace")
        except Exception:
            content = "<binary>"
        mime, _ = mimetypes.guess_type(str(file_path))
        return {
            "name": file_path.name,
            "path": str(file_path.relative_to(_get_session_root(ctx))),
            "size": size,
            "mime": mime or "application/octet-stream",
            "content": content,
        }
