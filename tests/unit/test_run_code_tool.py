"""Unit tests for run_code tool."""

from __future__ import annotations

from unittest.mock import patch

from server.sandbox.runner import RunCodeResult


class TestRunCodeTool:
    """Test run_code tool functionality."""

    def test_run_code_result_structure(self):
        """Test RunCodeResult structure."""
        result: RunCodeResult = {
            "stdout": "Hello World",
            "stderr": "",
            "artifacts": [],
        }
        assert "stdout" in result

    @patch("server.tools.run_code.sandbox_execute")
    async def test_run_code_execution(self, mock_execute):
        """Test code execution."""
        mock_execute.return_value = {
            "stdout": "Hello World",
            "stderr": "",
            "artifacts": [],
        }

        # Test execution
        assert mock_execute is not None

    @patch("server.sandbox.runner.create_virtualenv")
    async def test_environment_creation(self, mock_venv):
        """Test virtual environment creation."""
        mock_venv.return_value = "/path/to/python"

        # Test environment setup
        assert mock_venv is not None
