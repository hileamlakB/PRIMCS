"""Orchestrate sandbox execution of untrusted Python code."""

import asyncio
import mimetypes
import shutil
import textwrap
from typing import TypedDict

from server.config import TIMEOUT_SECONDS, TMP_DIR
from server.sandbox.downloader import download_files
from server.sandbox.env import create_virtualenv

__all__ = ["run_code"]


# Precise schema for each artifact entry.
class ArtifactMeta(TypedDict):
    name: str
    relative_path: str
    size: int
    mime: str


# Typed return for run_code results.
class RunCodeResult(TypedDict, total=False):
    """Result of running code in the sandbox.
    Optionally includes a feedback field with suggestions or warnings (list of strings).
    """

    stdout: str
    stderr: str
    artifacts: list[ArtifactMeta]
    feedback: str


async def run_code(
    *,
    code: str,
    requirements: list[str],
    files: list[dict[str, str]],
    run_id: str,
    session_id: str | None = None,
) -> RunCodeResult:
    """Execute *code* inside an isolated virtual-env and return captured output. Artifacts are returned as paths relative to the output directory. Only files inside output/ are included."""

    if session_id:
        # Persist workspace for the lifetime of the client session.
        work = TMP_DIR / f"session_{session_id}"
        work.mkdir(parents=True, exist_ok=True)
    else:
        # Legacy per-run workspace (stateless behaviour).
        work = TMP_DIR / f"run_{run_id}"
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True, exist_ok=True)

    # Ensure mounts directory exists for all modes.
    (work / "mounts").mkdir(parents=True, exist_ok=True)
    # Directory where user code should place output/artifacts.
    (work / "output").mkdir(parents=True, exist_ok=True)

    await download_files(files, work / "mounts")

    py = await create_virtualenv(requirements, work)

    script_name = f"script_{run_id}.py" if session_id else "script.py"
    script = work / script_name
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
    except TimeoutError as err:
        proc.kill()
        await proc.wait()
        msg = f"Execution timed out after {TIMEOUT_SECONDS}s"
        raise RuntimeError(msg) from err

    # Collect artifacts inside the output directory.
    artifacts: list[ArtifactMeta] = []
    output_dir = work / "output"
    for p in output_dir.rglob("*"):
        if p.is_file():
            try:
                rel_path = p.relative_to(output_dir)
            except ValueError:
                continue  # skip files not in output_dir
            size = p.stat().st_size
            mime, _ = mimetypes.guess_type(str(p))
            artifacts.append(
                {
                    "name": rel_path.name,
                    "relative_path": rel_path.as_posix(),
                    "size": size,
                    "mime": mime or "application/octet-stream",
                }
            )

    return {"stdout": out.decode(), "stderr": err.decode(), "artifacts": artifacts}
