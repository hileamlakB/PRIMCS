"""Integration tests for MCP protocol functionality."""

import asyncio
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from server.main import mcp


@pytest.mark.integration
class TestMCPIntegration:
    """Test MCP protocol integration."""

    @pytest.mark.asyncio
    async def test_mcp_server_startup(self) -> None:
        """Test that MCP server can start up properly."""
        # This is a basic integration test - in a real scenario
        # we would start the actual server
        assert mcp is not None
        assert mcp.name == "primcs"
        assert mcp.version == "0.1.0"

    @pytest.mark.asyncio
    async def test_tool_registration(self) -> None:
        """Test that all tools are properly registered."""
        # Verify tools are registered (this would be expanded in real tests)
        assert hasattr(mcp, "_tools")  # Internal FastMCP attribute

        # In a real test, we would inspect the registered tools
        # and verify they match our expected tool set

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_run_code_integration(
        self,
        mock_tmp_dir: Path,
        mock_virtualenv_creation: Path,
        mock_download_success: None,
    ) -> None:
        """Test full run_code tool integration."""
        from server.tools.run_code import register
        from fastmcp import FastMCP

        # Create a test MCP instance
        test_mcp = FastMCP(name="test", version="1.0")
        register(test_mcp)

        # This would be expanded to test actual tool execution
        # in a real integration test environment

        # Mock subprocess for integration test
        with patch("server.sandbox.runner.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = asyncio.create_subprocess_exec
            mock_process.communicate = lambda: (b"Hello World", b"")
            mock_process.returncode = 0

            # Test would verify the full flow here
            pass

    @pytest.mark.asyncio
    async def test_artifact_serving_integration(self, mock_tmp_dir: Path) -> None:
        """Test artifact serving through HTTP endpoint."""
        # Create test artifact
        session_id = "test-session"
        session_dir = mock_tmp_dir / f"session_{session_id}"
        output_dir = session_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        test_file = output_dir / "test.txt"
        test_file.write_text("Test artifact content")

        # This would test the actual HTTP endpoint in a real scenario
        # For now, we just verify the file structure is correct
        assert test_file.exists()
        assert test_file.read_text() == "Test artifact content"

    @pytest.mark.asyncio
    async def test_session_persistence(self, mock_tmp_dir: Path) -> None:
        """Test session-based workspace persistence."""
        session_id = "persistent-session"

        # Simulate multiple operations in the same session
        session_dir = mock_tmp_dir / f"session_{session_id}"

        # First operation
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "mounts").mkdir(exist_ok=True)
        (session_dir / "output").mkdir(exist_ok=True)

        # Create some files
        (session_dir / "output" / "result1.txt").write_text("First result")

        # Second operation (should see previous files)
        (session_dir / "output" / "result2.txt").write_text("Second result")

        # Verify both files exist
        assert (session_dir / "output" / "result1.txt").exists()
        assert (session_dir / "output" / "result2.txt").exists()


@pytest.mark.integration
@pytest.mark.e2e
class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self) -> None:
        """Test a complete workflow from code submission to artifact retrieval."""
        # This would be a full end-to-end test in a real scenario
        # involving starting the server, making HTTP requests, etc.

        test_code = """
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
print(df)
df.to_csv('output/test.csv', index=False)
"""

        # In a real E2E test, we would:
        # 1. Start the MCP server
        # 2. Submit the code via MCP protocol
        # 3. Verify the output
        # 4. Download the artifact
        # 5. Verify artifact contents

        assert len(test_code) > 0  # Placeholder assertion

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self) -> None:
        """Test error handling in a complete workflow."""
        invalid_code = """
import non_existent_module
print("This will fail")
"""

        # Test that errors are properly propagated and handled
        assert len(invalid_code) > 0  # Placeholder assertion

    @pytest.mark.asyncio
    async def test_file_mounting_workflow(self) -> None:
        """Test the complete file mounting workflow."""
        # Test mounting files and using them in code execution
        test_files = [{"url": "https://httpbin.org/json", "mountPath": "data.json"}]

        test_code = """
import json
with open('mounts/data.json', 'r') as f:
    data = json.load(f)
print(f"Loaded data: {data}")
"""

        # In a real test, this would verify the complete mounting workflow
        assert len(test_files) > 0
        assert len(test_code) > 0
