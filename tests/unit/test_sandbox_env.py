"""Unit tests for server.sandbox.env module."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from server.sandbox.env import _DEFAULT_PACKAGES, create_virtualenv


class TestCreateVirtualenv:
    """Test virtual environment creation."""

    @pytest.mark.asyncio
    async def test_create_virtualenv_success(self, temp_dir: Path) -> None:
        """Test successful virtual environment creation."""
        requirements = ["numpy", "pandas"]

        with (
            patch("server.sandbox.env.venv") as mock_venv,
            patch(
                "server.sandbox.env.asyncio.create_subprocess_exec"
            ) as mock_subprocess,
        ):
            # Mock venv creation
            mock_builder = Mock()
            mock_venv.EnvBuilder.return_value = mock_builder

            # Mock subprocess for pip install
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            # Call function
            python_path = await create_virtualenv(requirements, temp_dir)

            # Verify venv creation
            mock_venv.EnvBuilder.assert_called_once_with(with_pip=True, clear=True)
            mock_builder.create.assert_called_once()

            # Verify pip install call
            mock_subprocess.assert_called_once()
            args = mock_subprocess.call_args[0]

            # Check that python executable path is correct
            expected_python = (
                temp_dir
                / "venv"
                / ("Scripts" if sys.platform.startswith("win") else "bin")
                / "python"
            )
            assert Path(args[0]) == expected_python
            assert args[1:4] == ("-m", "pip", "install")
            assert "--no-cache-dir" in args

            # Check that requirements include both custom and default packages
            install_args = args[4:]  # Skip python, -m, pip, install
            install_args = [arg for arg in install_args if arg != "--no-cache-dir"]

            expected_packages = list(dict.fromkeys(requirements + _DEFAULT_PACKAGES))
            for package in expected_packages:
                assert package in install_args

            # Check return value
            assert python_path == expected_python

    @pytest.mark.asyncio
    async def test_create_virtualenv_pip_failure(self, temp_dir: Path) -> None:
        """Test virtual environment creation with pip install failure."""
        requirements = ["invalid-package"]

        with (
            patch("server.sandbox.env.venv") as mock_venv,
            patch(
                "server.sandbox.env.asyncio.create_subprocess_exec"
            ) as mock_subprocess,
        ):
            # Mock venv creation
            mock_builder = Mock()
            mock_venv.EnvBuilder.return_value = mock_builder

            # Mock subprocess for pip install failure
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(
                return_value=(b"", b"ERROR: Could not find package")
            )
            mock_process.returncode = 1
            mock_subprocess.return_value = mock_process

            # Should raise RuntimeError
            with pytest.raises(RuntimeError, match="pip install failed"):
                _ = await create_virtualenv(requirements, temp_dir)

    @pytest.mark.asyncio
    async def test_create_virtualenv_no_requirements(self, temp_dir: Path) -> None:
        """Test virtual environment creation with no additional requirements."""
        requirements: list[str] = []

        with (
            patch("server.sandbox.env.venv") as mock_venv,
            patch(
                "server.sandbox.env.asyncio.create_subprocess_exec"
            ) as mock_subprocess,
        ):
            # Mock venv creation
            mock_builder = Mock()
            mock_venv.EnvBuilder.return_value = mock_builder

            # Mock subprocess for pip install
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            # Call function
            _ = await create_virtualenv(requirements, temp_dir)

            # Should still install default packages
            mock_subprocess.assert_called_once()
            args = mock_subprocess.call_args[0]
            install_args = args[4:]  # Skip python, -m, pip, install
            install_args = [arg for arg in install_args if arg != "--no-cache-dir"]

            for package in _DEFAULT_PACKAGES:
                assert package in install_args

    @pytest.mark.asyncio
    async def test_create_virtualenv_duplicate_requirements(
        self, temp_dir: Path
    ) -> None:
        """Test that duplicate requirements are deduplicated."""
        requirements = [
            "pandas",
            "numpy",
            "pandas",
        ]  # pandas is duplicated and also in defaults

        with (
            patch("server.sandbox.env.venv") as mock_venv,
            patch(
                "server.sandbox.env.asyncio.create_subprocess_exec"
            ) as mock_subprocess,
        ):
            # Mock venv creation
            mock_builder = Mock()
            mock_venv.EnvBuilder.return_value = mock_builder

            # Mock subprocess for pip install
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            # Call function
            _ = await create_virtualenv(requirements, temp_dir)

            # Check that duplicates are removed
            args = mock_subprocess.call_args[0]
            install_args = args[4:]  # Skip python, -m, pip, install
            install_args = [arg for arg in install_args if arg != "--no-cache-dir"]

            # pandas should appear only once
            pandas_count = install_args.count("pandas")
            assert pandas_count == 1

    def test_default_packages_constant(self) -> None:
        """Test that default packages are properly defined."""
        assert isinstance(_DEFAULT_PACKAGES, list)
        assert len(_DEFAULT_PACKAGES) > 0
        assert "pandas" in _DEFAULT_PACKAGES
        assert "openpyxl" in _DEFAULT_PACKAGES
        assert "requests" in _DEFAULT_PACKAGES

    @pytest.mark.asyncio
    async def test_create_virtualenv_windows_path(self, temp_dir: Path) -> None:
        """Test that Windows-style paths are handled correctly."""
        requirements = ["numpy"]

        with (
            patch("server.sandbox.env.venv") as mock_venv,
            patch(
                "server.sandbox.env.asyncio.create_subprocess_exec"
            ) as mock_subprocess,
            patch("server.sandbox.env.sys.platform", "win32"),
        ):
            # Mock venv creation
            mock_builder = Mock()
            mock_venv.EnvBuilder.return_value = mock_builder

            # Mock subprocess for pip install
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            # Call function
            python_path = await create_virtualenv(requirements, temp_dir)

            # Check that Windows path is used
            expected_python = temp_dir / "venv" / "Scripts" / "python"
            assert python_path == expected_python
