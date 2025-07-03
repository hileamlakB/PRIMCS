"""Unit tests for server.main module."""

from unittest.mock import Mock, patch

import pytest

from server.main import mcp


class TestMainModule:
    """Test main module functionality."""

    def test_mcp_instance_exists(self) -> None:
        """Test that MCP instance is created."""
        assert mcp is not None
        assert mcp.name == "primcs"

    def test_mcp_instance_type(self) -> None:
        """Test that MCP instance has correct type."""
        from fastmcp import FastMCP

        assert isinstance(mcp, FastMCP)

    @patch("server.tools.run_code.register")
    def test_tool_registration_called(self, mock_register: Mock) -> None:
        """Test that tool registration is called during import."""
        # Re-import the module to trigger registration
        import importlib
        import server.main

        importlib.reload(server.main)

        # Verify register was called with the MCP instance
        mock_register.assert_called_once()
        call_args = mock_register.call_args[0]
        assert len(call_args) == 1
        # The argument should be a FastMCP instance
        from fastmcp import FastMCP

        assert isinstance(call_args[0], FastMCP)

    def test_mcp_configuration(self) -> None:
        """Test MCP instance configuration."""
        assert mcp.name == "primcs"
        # FastMCP doesn't expose version as a public attribute
        # but we can verify other properties
        assert hasattr(mcp, "name")
        assert hasattr(mcp, "tool")

    def test_module_imports(self) -> None:
        """Test that required modules are imported successfully."""
        # Test that we can import all the required components
        from server.tools.run_code import register
        from fastmcp import FastMCP

        assert callable(register)
        assert FastMCP is not None
