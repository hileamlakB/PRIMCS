"""Orchestrate sandbox execution of untrusted Python code."""
from __future__ import annotations

import asyncio
import shutil
import textwrap
from pathlib import Path

from server.config import TIMEOUT_SECONDS, TMP_DIR
from server.sandbox.downloader import download_files
from server.sandbox.env import create_virtualenv

__all__ = ["run_code"]


async def run_code(
    *,
    code: str,
    requirements: list[str],
    files: list[dict[str, str]],
    run_id: str,
    logger,
) -> dict[str, str]:
    """Execute *code* inside an isolated virtual-env and return captured output."""

    work = TMP_DIR / f"run_{run_id}"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)

    await download_files(files, work / "mounts")

    py = await create_virtualenv(requirements, work)

    script = work / "script.py"
    script.write_text(textwrap.dedent(code))

    proc = await asyncio.create_subprocess_exec(
        str(py),
        str(script),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=work,
    )

    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise RuntimeError(f"Execution timed out after {TIMEOUT_SECONDS}s")

    return {"stdout": out.decode(), "stderr": err.decode(), "artifacts": []} 