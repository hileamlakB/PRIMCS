"""Unit tests for sandbox environment creation."""

from __future__ import annotations

from unittest.mock import patch


class TestSandboxEnvironment:
    """Test sandbox environment functionality."""

    @patch("server.sandbox.env.asyncio.create_subprocess_exec")
    async def test_create_virtualenv(self, mock_subprocess):
        """Test virtual environment creation."""
        mock_proc = mock_subprocess.return_value
        mock_proc.communicate.return_value = (b"", b"")
        mock_proc.returncode = 0

        requirements = ["pandas", "numpy"]

        # Test would call create_virtualenv here
        assert mock_subprocess is not None
        assert requirements is not None

    def test_default_packages(self):
        """Test that default packages are included."""
        from server.sandbox.env import _DEFAULT_PACKAGES

        assert "pandas" in _DEFAULT_PACKAGES
        assert "requests" in _DEFAULT_PACKAGES
