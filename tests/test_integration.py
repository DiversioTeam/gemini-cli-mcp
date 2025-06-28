"""Integration tests for the Gemini MCP server."""

import asyncio
from unittest.mock import patch

import pytest

from gemini_mcp.server import GeminiMCPServer
from gemini_mcp.tools import GeminiTools


class TestIntegration:
    """Integration tests for real-world scenarios."""

    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, mock_gemini_cli):
        """Test handling of Gemini CLI authentication errors."""
        tools = GeminiTools()

        # Mock subprocess to simulate authentication error
        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = asyncio.create_task(self._mock_auth_error_process())
            mock_create.return_value = await mock_process

            with pytest.raises(RuntimeError, match="not authenticated|login required|authentication failed"):
                await tools._run_gemini_command("Test prompt")

    async def _mock_auth_error_process(self):
        """Helper to create a mock process that returns auth error."""
        class MockProcess:
            returncode = 1

            async def communicate(self, input=None):
                return (
                    b"",
                    b"Error: User not authenticated. Please run 'gemini auth login' first."
                )

        return MockProcess()

    @pytest.mark.asyncio
    async def test_file_not_found_error(self, mock_gemini_cli, temp_directory):
        """Test handling of file not found errors."""
        tools = GeminiTools(allowed_directories=[str(temp_directory)])

        with pytest.raises(ValueError, match="File does not exist"):
            await tools._run_gemini_command(
                "Analyze this",
                files=[str(temp_directory / "nonexistent.txt")]
            )

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, mock_gemini_cli, mock_subprocess):
        """Test that multiple tools can be called concurrently."""
        mock_create, mock_process = mock_subprocess
        server = GeminiMCPServer()

        # Create multiple concurrent tool calls
        tasks = []
        for i in range(5):
            task = server.tools.call_tool(
                "gemini_prompt",
                {"prompt": f"Question {i}"}
            )
            tasks.append(task)

        # All should complete successfully
        results = await asyncio.gather(*tasks)
        assert len(results) == 5
        for result in results:
            assert result == "Mocked Gemini output"

    @pytest.mark.asyncio
    async def test_large_file_handling(self, mock_gemini_cli, mock_subprocess, tmp_path):
        """Test handling of large files."""
        mock_create, mock_process = mock_subprocess

        # Create a large file
        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * 1_000_000)  # 1MB file

        tools = GeminiTools(allowed_directories=[str(tmp_path)])

        # Mock aiofiles for the test
        with patch("aiofiles.open") as mock_aiofiles:
            mock_file = asyncio.create_task(self._mock_async_file(str(large_file)))
            mock_aiofiles.return_value = await mock_file

            result = await tools._run_gemini_command(
                "Summarize this",
                files=[str(large_file)]
            )

            assert result == "Mocked Gemini output"

    async def _mock_async_file(self, filepath):
        """Helper to create a mock async file."""
        class MockAsyncFile:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def write(self, data):
                pass

            async def read(self):
                return f"{filepath}\n"

        return MockAsyncFile()

    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_gemini_cli):
        """Test handling of command timeouts."""
        tools = GeminiTools()

        # Mock subprocess to simulate a hanging process
        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = asyncio.create_task(self._mock_hanging_process())
            mock_create.return_value = await mock_process

            # This should eventually timeout or handle the hanging process
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(
                    tools._run_gemini_command("Test prompt"),
                    timeout=0.1  # Short timeout for test
                )

    async def _mock_hanging_process(self):
        """Helper to create a mock process that hangs."""
        class MockProcess:
            returncode = None

            async def communicate(self, input=None):
                # Simulate a hanging process
                await asyncio.sleep(10)
                return (b"", b"")

        return MockProcess()


class TestSecurityIntegration:
    """Security-focused integration tests."""

    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, mock_gemini_cli, tmp_path):
        """Test that path traversal attacks are prevented."""
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()
        secret_dir = tmp_path / "secret"
        secret_dir.mkdir()
        (secret_dir / "secret.txt").write_text("SECRET DATA")

        tools = GeminiTools(allowed_directories=[str(safe_dir)])

        # Various path traversal attempts
        malicious_paths = [
            str(safe_dir / ".." / "secret" / "secret.txt"),
            "../secret/secret.txt",
            str(secret_dir / "secret.txt"),
            "/etc/passwd",
            "~/.ssh/id_rsa",
        ]

        for path in malicious_paths:
            with pytest.raises(ValueError, match="outside allowed directories"):
                tools._validate_file_path(path)

    @pytest.mark.asyncio
    async def test_command_injection_prevention(self, mock_gemini_cli, mock_subprocess):
        """Test that command injection is prevented."""
        mock_create, mock_process = mock_subprocess
        tools = GeminiTools()

        # Attempt command injection through various parameters
        malicious_prompts = [
            "'; rm -rf /; echo '",
            "$(whoami)",
            "`id`",
            "& calc.exe &",
        ]

        for prompt in malicious_prompts:
            await tools._run_gemini_command(prompt)

            # Verify the command was properly escaped
            call_args = mock_create.call_args[0]
            # The prompt should be passed as a single argument, not interpreted
            assert prompt in call_args
            # Should not have shell=True or similar unsafe execution
            assert all(isinstance(arg, str) for arg in call_args)
