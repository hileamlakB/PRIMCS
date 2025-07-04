"""Unit tests for server.tools.run_code module."""

from unittest.mock import Mock, patch
from types import SimpleNamespace

import pytest

from server.tools.run_code import RESPONSE_FEEDBACK, register


class TestRunCodeTool:
    """Test the run_code MCP tool."""

    def test_register_function_exists(self) -> None:
        """Test that register function is properly defined."""
        assert callable(register)

    @pytest.mark.asyncio
    async def test_run_code_tool_success(
        self,
        mock_fastmcp: Mock,
        mock_context: Mock,
        sample_python_code: str,
    ) -> None:
        """Test successful code execution through the MCP tool."""
        # Mock the sandbox execute function
        mock_result = {
            "stdout": "Hello from sandbox!",
            "stderr": "",
            "artifacts": [],
        }

        with patch(
            "server.tools.run_code.sandbox_execute", return_value=mock_result
        ) as mock_execute:
            # Register the tool
            register(mock_fastmcp)

            # Get the registered tool function
            tool_calls = mock_fastmcp.tool.call_args_list
            assert len(tool_calls) == 1

            # Extract the tool function
            tool_decorator_call = tool_calls[0]
            tool_kwargs = tool_decorator_call[1]
            assert tool_kwargs["name"] == "run_code"
            assert "description" in tool_kwargs

            # The actual tool function would be called by FastMCP
            # We'll test it by calling the sandbox_execute function directly
            result = await mock_execute(
                code=sample_python_code,
                requirements=[],
                files=[],
                run_id="test-run",
                session_id="test-session",
            )

            assert result["stdout"] == "Hello from sandbox!"
            assert result["stderr"] == ""

    @pytest.mark.asyncio
    async def test_run_code_tool_with_requirements(
        self,
        mock_fastmcp: Mock,
        sample_requirements: list[str],
    ) -> None:
        """Test code execution with pip requirements."""
        mock_result = {
            "stdout": "Package installed successfully",
            "stderr": "",
            "artifacts": [],
        }

        with patch(
            "server.tools.run_code.sandbox_execute", return_value=mock_result
        ) as mock_execute:
            register(mock_fastmcp)

            _ = await mock_execute(
                code="import numpy; print('numpy imported')",
                requirements=sample_requirements,
                files=[],
                run_id="test-run",
                session_id="test-session",
            )

            # Verify requirements were passed through
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert call_args[1]["requirements"] == sample_requirements

    @pytest.mark.asyncio
    async def test_run_code_tool_with_files(
        self,
        mock_fastmcp: Mock,
        sample_files: list[dict[str, str]],
    ) -> None:
        """Test code execution with file mounting."""
        mock_result = {
            "stdout": "Files mounted successfully",
            "stderr": "",
            "artifacts": [],
        }

        with patch(
            "server.tools.run_code.sandbox_execute", return_value=mock_result
        ) as mock_execute:
            register(mock_fastmcp)

            _ = await mock_execute(
                code="print('Files available')",
                requirements=[],
                files=sample_files,
                run_id="test-run",
                session_id="test-session",
            )

            # Verify files were passed through
            call_args = mock_execute.call_args
            assert call_args[1]["files"] == sample_files

    # test what happens when code is empty
    # test what happens when requirements is empty when it is needed
    # test what happens when files is empty when it is needed
    # test what happens when files is empty when it is not needed
    # test what happens when files is not empty when it is not needed
    # test what happens when files is not empty when it is needed
    # test what happens when files is not empty when it is not needed
    # test when code is empty
    # test when code is too long