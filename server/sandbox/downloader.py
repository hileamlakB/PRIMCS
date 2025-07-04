"""Download remote files to the sandbox run directory."""

import asyncio
from pathlib import Path

import aiohttp

__all__ = ["download_files"]


async def _fetch(session: aiohttp.ClientSession, url: str, path: Path) -> None:
    async with session.get(url) as resp:
        resp.raise_for_status()
        path.write_bytes(await resp.read())
    # Make the file read-only
    try:
        path.chmod(0o444)
    except PermissionError:  # fallback on platforms that forbid chmod inside container
        pass


async def download_files(files: list[dict[str, str]], dest: Path) -> list[Path]:
    """Download *files* concurrently into *dest*.

    Each element in *files* must be a dict with keys ``url`` and **``mountPath``** (required).

    Returns list of local paths (relative to *dest*).
    """
    if not files:
        return []

    dest.mkdir(parents=True, exist_ok=True)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for meta in files:
            url = meta["url"]
            if "mountPath" not in meta or not meta["mountPath"]:
                raise ValueError(
                    "Each file entry must include a non-empty 'mountPath' key."
                )

            relative = Path(meta["mountPath"])
            local = dest / relative
            local.parent.mkdir(parents=True, exist_ok=True)
            tasks.append(_fetch(session, url, local))
        await asyncio.gather(*tasks)

    return [dest / Path(f["mountPath"]) for f in files]
