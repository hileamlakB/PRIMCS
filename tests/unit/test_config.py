"""Unit tests for server.config module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from server import config


class TestConfig:
    """Test configuration management."""

    def test_default_tmp_dir(self) -> None:
        """Test default TMP_DIR configuration."""
        with patch.dict(os.environ, {}, clear=True):
            # Re-import to get fresh configuration
            import importlib

            importlib.reload(config)

            expected_path = Path("/tmp/primcs")
            assert config.TMP_DIR == expected_path

    def test_custom_tmp_dir(self, tmp_path: Path) -> None:
        """Test custom TMP_DIR from environment variable."""
        custom_path = str(tmp_path / "custom_tmp")
        with patch.dict(os.environ, {"PRIMCS_TMP_DIR": custom_path}):
            import importlib

            importlib.reload(config)

            assert config.TMP_DIR == Path(custom_path)

    def test_default_timeout(self) -> None:
        """Test default timeout configuration."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib

            importlib.reload(config)

            assert config.TIMEOUT_SECONDS == 100

    def test_custom_timeout(self) -> None:
        """Test custom timeout from environment variable."""
        custom_timeout = "60"
        with patch.dict(os.environ, {"PRIMCS_TIMEOUT": custom_timeout}):
            import importlib

            importlib.reload(config)

            assert config.TIMEOUT_SECONDS == 60

    def test_default_max_output(self) -> None:
        """Test default max output configuration."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib

            importlib.reload(config)

            assert config.MAX_OUTPUT_BYTES == 1024 * 1024  # 1MB

    def test_custom_max_output(self) -> None:
        """Test custom max output from environment variable."""
        custom_max = "2048000"  # 2MB
        with patch.dict(os.environ, {"PRIMCS_MAX_OUTPUT": custom_max}):
            import importlib

            importlib.reload(config)

            assert config.MAX_OUTPUT_BYTES == 2048000

    def test_invalid_timeout_falls_back_to_default(self) -> None:
        """Test that invalid timeout values fall back to default."""
        with patch.dict(os.environ, {"PRIMCS_TIMEOUT": "invalid"}):
            with pytest.raises(ValueError):
                import importlib

                importlib.reload(config)

    def test_invalid_max_output_falls_back_to_default(self) -> None:
        """Test that invalid max output values fall back to default."""
        with patch.dict(os.environ, {"PRIMCS_MAX_OUTPUT": "invalid"}):
            with pytest.raises(ValueError):
                import importlib

                importlib.reload(config)

    def test_tmp_dir_creation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that TMP_DIR is created if it doesn't exist."""
        test_dir = tmp_path / "test_primcs"
        monkeypatch.setenv("PRIMCS_TMP_DIR", str(test_dir))

        import importlib

        importlib.reload(config)

        assert test_dir.exists()
        assert test_dir.is_dir()
