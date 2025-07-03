"""Unit tests for server.sandbox.runner module."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from server.sandbox.runner import run_code, ArtifactMeta, RunCodeResult


class TestRunCode:
    """Test code execution functionality."""

    @pytest.mark.asyncio
    async def test_run_code_success_with_session(
        self,
        mock_tmp_dir: Path,
        session_id: str,
        run_id: str,
        sample_python_code: str,
        mock_download_success: None,
        mock_virtualenv_creation: Path,
    ) -> None:
        """Test successful code execution with session persistence."""
        requirements = ["numpy"]
        files = [{"url": "https://example.com/data.csv", "mountPath": "data.csv"}]

        with patch("server.sandbox.runner.asyncio.create_subprocess_exec") as mock_subprocess:
            # Mock subprocess execution
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(
                return_value=(
                    b"Hello from sandbox!\nWorking directory: /tmp/session\n",
                    b"Warning: some warning\n",
                )
            )
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            # Create expected output file
            session_dir = mock_tmp_dir / f"session_{session_id}"
            output_dir = session_dir / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "test_output.txt").write_text("Test output file")

            # Call function
            result = await run_code(
                code=sample_python_code,
                requirements=requirements,
                files=files,
                run_id=run_id,
                session_id=session_id,
            )

            # Verify result structure
            assert isinstance(result, dict)
            assert "stdout" in result
            assert "stderr" in result
            assert "artifacts" in result

            # Verify output
            assert "Hello from sandbox!" in result["stdout"]
            assert "Warning: some warning" in result["stderr"]

            # Verify artifacts
            artifacts = result["artifacts"]
            assert len(artifacts) == 1
            artifact = artifacts[0]
            assert artifact["name"] == "test_output.txt"
            assert artifact["relative_path"] == "test_output.txt"
            assert artifact["size"] > 0
            assert "text" in artifact["mime"]

    @pytest.mark.asyncio
    async def test_run_code_success_without_session(
        self,
        mock_tmp_dir: Path,
        run_id: str,
        sample_python_code: str,
        mock_download_success: None,
        mock_virtualenv_creation: Path,
    ) -> None:
        """Test successful code execution without session (stateless)."""
        requirements: list[str] = []
        files: list[dict[str, str]] = []

        with patch("server.sandbox.runner.asyncio.create_subprocess_exec") as mock_subprocess:
            # Mock subprocess execution
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"Output without session", b""))
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            # Call function without session_id
            result = await run_code(
                code=sample_python_code,
                requirements=requirements,
                files=files,
                run_id=run_id,
                session_id=None,
            )

            # Verify result
            assert result["stdout"] == "Output without session"
            assert result["stderr"] == ""
            assert result["artifacts"] == []

    @pytest.mark.asyncio
    async def test_run_code_timeout(
        self,
        mock_tmp_dir: Path,
        run_id: str,
        sample_python_code: str,
        mock_download_success: None,
        mock_virtualenv_creation: Path,
    ) -> None:
        """Test code execution timeout handling."""
        with patch(
            "server.sandbox.runner.asyncio.create_subprocess_exec"
        ) as mock_subprocess, patch(
            "server.sandbox.runner.asyncio.wait_for"
        ) as mock_wait_for, patch(
            "server.sandbox.runner.create_virtualenv"
        ) as mock_create_venv:

            # Mock virtualenv creation to return the mocked python path
            mock_create_venv.return_value = mock_virtualenv_creation

            # Mock subprocess
            mock_process = AsyncMock()
            mock_process.kill = Mock(return_value=None)
            mock_process.wait = AsyncMock(return_value=None)
            mock_subprocess.return_value = mock_process

            # Mock timeout on the wait_for call
            mock_wait_for.side_effect = asyncio.TimeoutError()

            # Should raise RuntimeError
            with pytest.raises(RuntimeError, match="Execution timed out"):
                await run_code(
                    code=sample_python_code,
                    requirements=[],
                    files=[],
                    run_id=run_id,
                    session_id=None,
                )

            # Verify process was killed
            mock_process.kill.assert_called_once()
            mock_process.wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_code_with_artifacts(
        self,
        mock_tmp_dir: Path,
        session_id: str,
        run_id: str,
        mock_download_success: None,
        mock_virtualenv_creation: Path,
    ) -> None:
        """Test code execution with multiple artifacts."""
        code = "print('Creating artifacts')"

        with patch("server.sandbox.runner.asyncio.create_subprocess_exec") as mock_subprocess:
            # Mock subprocess execution
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"Creating artifacts", b""))
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            # Create multiple output files
            session_dir = mock_tmp_dir / f"session_{session_id}"
            output_dir = session_dir / "output"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Create various file types
            (output_dir / "data.csv").write_text("col1,col2\n1,2\n3,4")
            (output_dir / "plot.png").write_bytes(b"\x89PNG\r\n\x1a\n")  # Fake PNG header
            (output_dir / "subdir").mkdir()
            (output_dir / "subdir" / "nested.txt").write_text("nested file")

            # Call function
            result = await run_code(
                code=code,
                requirements=[],
                files=[],
                run_id=run_id,
                session_id=session_id,
            )

            # Verify artifacts
            artifacts = result["artifacts"]
            assert len(artifacts) == 3

            # Check artifact details
            artifact_names = {a["name"] for a in artifacts}
            assert "data.csv" in artifact_names
            assert "plot.png" in artifact_names
            assert "nested.txt" in artifact_names

            # Check MIME types
            csv_artifact = next(a for a in artifacts if a["name"] == "data.csv")
            assert csv_artifact["mime"] == "text/csv"

            png_artifact = next(a for a in artifacts if a["name"] == "plot.png")
            assert png_artifact["mime"] == "image/png"

    @pytest.mark.asyncio
    async def test_run_code_script_naming(
        self,
        mock_tmp_dir: Path,
        session_id: str,
        run_id: str,
        mock_download_success: None,
        mock_virtualenv_creation: Path,
    ) -> None:
        """Test that script naming varies based on session presence."""
        code = "print('test')"

        with patch("server.sandbox.runner.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"test", b""))
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            # Test with session (should use run_id in script name)
            await run_code(
                code=code,
                requirements=[],
                files=[],
                run_id=run_id,
                session_id=session_id,
            )

            # Check script name includes run_id
            session_dir = mock_tmp_dir / f"session_{session_id}"
            expected_script = session_dir / f"script_{run_id}.py"
            assert expected_script.exists()

            # Test without session (should use generic script name)
            await run_code(
                code=code,
                requirements=[],
                files=[],
                run_id=run_id,
                session_id=None,
            )

            # Check generic script name
            run_dir = mock_tmp_dir / f"run_{run_id}"
            expected_script = run_dir / "script.py"
            assert expected_script.exists()

    @pytest.mark.asyncio
    async def test_run_code_directory_creation(
        self,
        mock_tmp_dir: Path,
        session_id: str,
        run_id: str,
        mock_download_success: None,
        mock_virtualenv_creation: Path,
    ) -> None:
        """Test that required directories are created."""
        code = "print('test')"

        with patch("server.sandbox.runner.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"test", b""))
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            # Call with session
            await run_code(
                code=code,
                requirements=[],
                files=[],
                run_id=run_id,
                session_id=session_id,
            )

            # Verify directories exist
            session_dir = mock_tmp_dir / f"session_{session_id}"
            assert session_dir.exists()
            assert (session_dir / "mounts").exists()
            assert (session_dir / "output").exists()

    def test_artifact_meta_type(self) -> None:
        """Test ArtifactMeta type definition."""
        artifact: ArtifactMeta = {
            "name": "test.txt",
            "relative_path": "test.txt",
            "size": 100,
            "mime": "text/plain",
        }

        assert artifact["name"] == "test.txt"
        assert artifact["relative_path"] == "test.txt"
        assert artifact["size"] == 100
        assert artifact["mime"] == "text/plain"

    def test_run_code_result_type(self) -> None:
        """Test RunCodeResult type definition."""
        result: RunCodeResult = {
            "stdout": "test output",
            "stderr": "test error",
            "artifacts": [],
        }

        assert result["stdout"] == "test output"
        assert result["stderr"] == "test error"
        assert result["artifacts"] == []

        # Test with feedback
        result_with_feedback: RunCodeResult = {
            "stdout": "",
            "stderr": "",
            "artifacts": [],
            "feedback": "No output detected",
        }

        assert result_with_feedback["feedback"] == "No output detected"
