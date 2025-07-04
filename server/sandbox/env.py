"""Utility helpers for creating isolated virtual environments."""

import asyncio
import sys
import venv
from pathlib import Path

# Default libraries always installed in every sandbox environment.
_DEFAULT_PACKAGES: list[str] = ["pandas", "openpyxl", "requests"]


async def create_virtualenv(requirements: list[str], run_dir: Path) -> Path:
    """Create a venv in run_dir/venv and install *requirements*."""
    venv_dir = run_dir / "venv"
    venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)

    python = (
        venv_dir / ("Scripts" if sys.platform.startswith("win") else "bin") / "python"
    )

    # Combine caller-specified requirements with default packages.
    all_requirements = list(dict.fromkeys(requirements + _DEFAULT_PACKAGES))

    if all_requirements:
        proc = await asyncio.create_subprocess_exec(
            str(python),
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            *all_requirements,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, err = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"pip install failed: {err.decode()}")

    return python
