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

    Returns list of local paths (relative to *dest*).
    """
    if not files:
        return []

    dest.mkdir(parents=True, exist_ok=True)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for meta in files:
            url = meta["url"]
            relative = Path(meta.get("mountPath") or Path(url).name)
            local = dest / relative
            local.parent.mkdir(parents=True, exist_ok=True)
            tasks.append(_fetch(session, url, local))
        await asyncio.gather(*tasks)

    return [dest / (f.get("mountPath") or Path(f["url"]).name) for f in files] 