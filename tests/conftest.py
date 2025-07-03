"""Shared pytest fixtures for PRIMS testing."""

import tempfile
import shutil
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock

import pytest
from fastmcp import FastMCP
from httpx import AsyncClient

from server.config import TMP_DIR


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test isolation."""
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_tmp_dir(temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Mock the global TMP_DIR with a temporary directory."""
    monkeypatch.setattr("server.config.TMP_DIR", temp_dir)
    monkeypatch.setattr("server.sandbox.runner.TMP_DIR", temp_dir)
    monkeypatch.setattr("server.tools.workspace_inspect.TMP_DIR", temp_dir)
    return temp_dir


@pytest.fixture
def session_id() -> str:
    """Provide a test session ID."""
    return "test-session-123"


@pytest.fixture
def run_id() -> str:
    """Provide a test run ID."""
    return "test-run-456"


@pytest.fixture
def sample_python_code() -> str:
    """Provide sample Python code for testing."""
    return """
import pandas as pd
import os

# Test basic functionality
print("Hello from sandbox!")
print(f"Working directory: {os.getcwd()}")

# Test file operations
with open("output/test_output.txt", "w") as f:
    f.write("Test output file")

# Test pandas
df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
print(df.head())
"""


@pytest.fixture
def invalid_python_code() -> str:
    """Provide invalid Python code for testing error handling."""
    return """
import non_existent_module
print("This should fail")
invalid_syntax here
"""


@pytest.fixture
def mock_fastmcp() -> Mock:
    """Create a mock FastMCP instance for testing."""
    mock_mcp = Mock()
    mock_mcp.name = "test-prims"
    mock_mcp.version = "0.1.0"
    mock_mcp.tool = Mock()
    return mock_mcp


@pytest.fixture
def mock_context() -> Mock:
    """Create a mock Context for testing."""
    context = Mock()
    context.session_id = "test-session-123"
    context.request_id = "test-request-456"
    context.request_context.request = Mock()
    context.request_context.request.headers = {"mcp-session-id": "test-session-123"}
    return context


@pytest.fixture
async def http_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an HTTP client for integration testing."""
    async with AsyncClient() as client:
        yield client


@pytest.fixture
def mock_subprocess_success() -> Mock:
    """Mock successful subprocess execution."""
    mock_process = AsyncMock()
    mock_process.communicate = AsyncMock(return_value=(b"stdout output", b"stderr output"))
    mock_process.returncode = 0
    mock_process.wait = AsyncMock(return_value=None)
    mock_process.kill = Mock(return_value=None)
    return mock_process


@pytest.fixture
def mock_subprocess_failure() -> Mock:
    """Mock failed subprocess execution."""
    mock_process = AsyncMock()
    mock_process.communicate = AsyncMock(return_value=(b"", b"Error: command failed"))
    mock_process.returncode = 1
    mock_process.wait = AsyncMock(return_value=None)
    mock_process.kill = Mock(return_value=None)
    return mock_process


@pytest.fixture
def sample_requirements() -> list[str]:
    """Provide sample pip requirements for testing."""
    return ["numpy>=1.20.0", "matplotlib>=3.5.0"]


@pytest.fixture
def sample_files() -> list[dict[str, str]]:
    """Provide sample file mounting configuration for testing."""
    return [
        {"url": "https://example.com/data.csv", "mountPath": "data/input.csv"},
        {"url": "https://example.com/config.json", "mountPath": "config.json"},
    ]


@pytest.fixture
def mock_download_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock successful file downloads."""

    async def mock_download_files(files: list[dict[str, str]], mount_dir: Path) -> list[Path]:
        paths = []
        for file_info in files:
            mount_path = mount_dir / file_info["mountPath"]
            mount_path.parent.mkdir(parents=True, exist_ok=True)
            mount_path.write_text(f"Mock content for {file_info['url']}")
            paths.append(mount_path)
        return paths

    monkeypatch.setattr("server.sandbox.runner.download_files", mock_download_files)


@pytest.fixture
def mock_virtualenv_creation(monkeypatch: pytest.MonkeyPatch, temp_dir: Path) -> Path:
    """Mock virtual environment creation."""
    python_path = temp_dir / "venv" / "bin" / "python"
    python_path.parent.mkdir(parents=True, exist_ok=True)
    python_path.write_text("#!/usr/bin/env python3\n# Mock Python executable")
    python_path.chmod(0o755)

    async def mock_create_virtualenv(requirements: list[str], run_dir: Path) -> Path:
        return python_path

    monkeypatch.setattr("server.sandbox.env.create_virtualenv", mock_create_virtualenv)
    return python_path
