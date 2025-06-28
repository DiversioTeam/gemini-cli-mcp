"""Tests for the GeminiTools class."""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from gemini_mcp.tools import DEFAULT_GEMINI_MODEL, GeminiTools


class TestGeminiTools:
    """Test cases for GeminiTools."""

    def test_initialization_without_gemini_cli(self):
        """Test initialization fails when Gemini CLI is not found."""
        with (
            patch("shutil.which", return_value=None),
            pytest.raises(RuntimeError, match="Gemini CLI not found"),
        ):
            GeminiTools()

    def test_initialization_with_gemini_cli(self, mock_gemini_cli):
        """Test successful initialization when Gemini CLI is found."""
        tools = GeminiTools()
        assert tools.gemini_path == "/usr/local/bin/gemini"
        assert len(tools.allowed_directories) == 1
        assert tools.allowed_directories[0] == Path.cwd()

    def test_initialization_with_custom_directories(self, mock_gemini_cli, tmp_path):
        """Test initialization with custom allowed directories."""
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()

        tools = GeminiTools(allowed_directories=[str(custom_dir)])
        assert len(tools.allowed_directories) == 1
        assert tools.allowed_directories[0] == custom_dir.resolve()

    def test_get_tool_definitions(self, mock_gemini_cli):
        """Test that all tool definitions are properly returned."""
        tools = GeminiTools()
        definitions = tools.get_tool_definitions()

        assert len(definitions) == 4
        tool_names = [tool.name for tool in definitions]
        assert "gemini_prompt" in tool_names
        assert "gemini_research" in tool_names
        assert "gemini_analyze_code" in tool_names
        assert "gemini_summarize" in tool_names

        # Check that default model is used consistently
        for tool in definitions:
            if "model" in tool.inputSchema["properties"]:
                assert tool.inputSchema["properties"]["model"]["default"] == DEFAULT_GEMINI_MODEL

    def test_validate_file_path_valid(self, mock_gemini_cli, temp_directory):
        """Test file path validation with valid paths."""
        tools = GeminiTools(allowed_directories=[str(temp_directory)])

        # Test absolute path
        valid_path = temp_directory / "test1.txt"
        result = tools._validate_file_path(str(valid_path))
        assert result == valid_path.resolve()

        # Test path within subdirectory
        subdir_file = temp_directory / "subdir" / "test3.md"
        result = tools._validate_file_path(str(subdir_file))
        assert result == subdir_file.resolve()

    def test_validate_file_path_invalid(self, mock_gemini_cli, temp_directory):
        """Test file path validation with invalid paths."""
        tools = GeminiTools(allowed_directories=[str(temp_directory)])

        # Test path outside allowed directory
        with pytest.raises(ValueError, match="outside allowed directories"):
            tools._validate_file_path("/etc/passwd")

        # Test path traversal attempt
        with pytest.raises(ValueError, match="outside allowed directories"):
            tools._validate_file_path(str(temp_directory / ".." / ".." / "etc" / "passwd"))

    @pytest.mark.asyncio()
    async def test_run_gemini_command_simple(self, mock_gemini_cli, mock_subprocess):
        """Test running a simple Gemini command."""
        mock_create, mock_process = mock_subprocess
        tools = GeminiTools()

        result = await tools._run_gemini_command("Test prompt")

        # Verify subprocess was called correctly
        mock_create.assert_called_once()
        call_args = mock_create.call_args[0]
        assert call_args[0] == "/usr/local/bin/gemini"
        assert "-m" in call_args
        assert DEFAULT_GEMINI_MODEL in call_args
        assert "-p" in call_args
        assert "Test prompt" in call_args

        assert result == "Mocked Gemini output"

    @pytest.mark.asyncio()
    async def test_run_gemini_command_with_files(
        self, mock_gemini_cli, mock_subprocess, temp_directory
    ):
        """Test running Gemini command with file inputs."""
        mock_create, mock_process = mock_subprocess
        tools = GeminiTools(allowed_directories=[str(temp_directory)])

        test_file = temp_directory / "test1.txt"

        # Mock aiofiles to avoid actual file I/O in tests
        with patch("aiofiles.open") as mock_aiofiles:
            mock_file = AsyncMock()
            mock_file.__aenter__.return_value = mock_file
            mock_file.write = AsyncMock()
            mock_file.read = AsyncMock(return_value=f"{test_file}\n")
            mock_aiofiles.return_value = mock_file

            await tools._run_gemini_command("Analyze this file", files=[str(test_file)])

        # Verify the -a flag was added
        call_args = mock_create.call_args[0]
        assert "-a" in call_args

        # Verify stdin was provided with file list
        mock_process.communicate.assert_called_once()
        stdin_data = mock_process.communicate.call_args[1]["input"]
        assert test_file.name in stdin_data.decode()

    @pytest.mark.asyncio()
    async def test_run_gemini_command_error(self, mock_gemini_cli, mock_subprocess):
        """Test handling of Gemini command errors."""
        mock_create, mock_process = mock_subprocess
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b"", b"Error: Invalid prompt")

        tools = GeminiTools()

        with pytest.raises(RuntimeError, match="Gemini CLI error: Error: Invalid prompt"):
            await tools._run_gemini_command("Bad prompt")

    @pytest.mark.asyncio()
    async def test_gemini_prompt(self, mock_gemini_cli, mock_subprocess):
        """Test the gemini_prompt tool."""
        mock_create, mock_process = mock_subprocess
        tools = GeminiTools()

        await tools._gemini_prompt(
            {"prompt": "What is Python?", "context": "Programming languages"}
        )

        # Verify the prompt was properly formatted
        call_args = mock_create.call_args[0]
        prompt_index = call_args.index("-p") + 1
        assert "Programming languages" in call_args[prompt_index]
        assert "What is Python?" in call_args[prompt_index]

    @pytest.mark.asyncio()
    async def test_gemini_summarize_validation(self, mock_gemini_cli):
        """Test that summarize requires either content or files."""
        tools = GeminiTools()

        # Test with neither content nor files
        result = await tools._gemini_summarize({})
        assert "Error: Either content or files must be provided" in result

    @pytest.mark.asyncio()
    async def test_call_tool_unknown(self, mock_gemini_cli):
        """Test calling an unknown tool raises ValueError."""
        tools = GeminiTools()

        with pytest.raises(ValueError, match="Unknown tool: unknown_tool"):
            await tools.call_tool("unknown_tool", {})

    @pytest.mark.asyncio()
    async def test_temp_file_cleanup(self, mock_gemini_cli, mock_subprocess, temp_directory):
        """Test that temporary files are cleaned up even on error."""
        mock_create, mock_process = mock_subprocess
        tools = GeminiTools(allowed_directories=[str(temp_directory)])

        test_file = temp_directory / "test1.txt"

        # Track temp files created
        temp_files_created = []
        original_mkstemp = tempfile.mkstemp

        def track_mkstemp(*args, **kwargs):
            fd, path = original_mkstemp(*args, **kwargs)
            temp_files_created.append(path)
            return fd, path

        with (
            patch("tempfile.mkstemp", side_effect=track_mkstemp),
            patch("aiofiles.open") as mock_aiofiles,
        ):
            mock_file = AsyncMock()
            mock_file.__aenter__.return_value = mock_file
            mock_file.write = AsyncMock()
            mock_aiofiles.return_value = mock_file

            # Force an error during command execution
            mock_process.communicate.side_effect = Exception("Command failed")

            with pytest.raises(Exception, match="Command failed"):
                await tools._run_gemini_command("Test", files=[str(test_file)])

        # Verify temp files were cleaned up
        for temp_file in temp_files_created:
            assert not os.path.exists(temp_file)
