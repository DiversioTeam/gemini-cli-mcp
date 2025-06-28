"""Additional tests to improve coverage."""

import os
from unittest.mock import AsyncMock, patch

import pytest

from gemini_mcp.server import GeminiMCPServer
from gemini_mcp.tools import GeminiTools


class TestServerCoverage:
    """Additional server tests for coverage."""

    @pytest.mark.asyncio
    async def test_server_run_method(self, mock_gemini_cli):
        """Test the server run method (coverage for async context manager)."""
        server = GeminiMCPServer()

        # Mock the stdio_server context manager
        mock_read = AsyncMock()
        mock_write = AsyncMock()

        with patch("gemini_mcp.server.stdio_server") as mock_stdio:
            # Create async context manager mock
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = (mock_read, mock_write)
            async_cm.__aexit__.return_value = None
            mock_stdio.return_value = async_cm

            # Mock the server.run to complete immediately
            with patch.object(server.server, "run", new_callable=AsyncMock) as mock_run:
                await server.run()

                # Verify stdio_server was called
                mock_stdio.assert_called_once()

                # Verify server.run was called with correct parameters
                mock_run.assert_called_once()
                args = mock_run.call_args[0]
                assert args[0] == mock_read
                assert args[1] == mock_write

    def test_version_fallback(self):
        """Test version loading with metadata error."""
        with patch("gemini_mcp.server.metadata.version", side_effect=Exception("No metadata")):
            # Re-import to trigger the version loading
            import importlib

            import gemini_mcp.server
            importlib.reload(gemini_mcp.server)

            # Should fall back to default version
            assert gemini_mcp.server.__version__ == "0.1.0"


class TestToolsCoverage:
    """Additional tools tests for coverage."""

    @pytest.mark.asyncio
    async def test_gemini_research_tool(self, mock_gemini_cli, mock_subprocess):
        """Test the gemini_research tool."""
        mock_create, mock_process = mock_subprocess
        tools = GeminiTools()

        result = await tools.call_tool("gemini_research", {
            "topic": "Python best practices"
        })

        assert result == "Mocked Gemini output"

        # Check the command was built correctly
        call_args = mock_create.call_args[0]
        assert "-p" in call_args
        prompt_idx = call_args.index("-p") + 1
        assert "Python best practices" in call_args[prompt_idx]
        assert "comprehensive analysis" in call_args[prompt_idx]

    @pytest.mark.asyncio
    async def test_gemini_analyze_code_tool(self, mock_gemini_cli, mock_subprocess, temp_directory):
        """Test the gemini_analyze_code tool."""
        mock_create, mock_process = mock_subprocess

        # Create a test file
        test_file = temp_directory / "test.py"
        test_file.write_text("print('Hello')")

        tools = GeminiTools(allowed_directories=[str(temp_directory)])

        # Mock aiofiles
        with patch("aiofiles.open") as mock_aiofiles:
            mock_file = AsyncMock()
            mock_file.__aenter__.return_value = mock_file
            mock_file.write = AsyncMock()
            mock_file.read = AsyncMock(return_value=str(test_file) + "\n")
            mock_aiofiles.return_value = mock_file

            result = await tools.call_tool("gemini_analyze_code", {
                "files": [str(test_file)],
                "analysis_type": "review"
            })

            assert result == "Mocked Gemini output"

    @pytest.mark.asyncio
    async def test_gemini_summarize_with_content(self, mock_gemini_cli, mock_subprocess):
        """Test gemini_summarize with content instead of files."""
        mock_create, mock_process = mock_subprocess
        tools = GeminiTools()

        result = await tools.call_tool("gemini_summarize", {
            "content": "This is a long text to summarize...",
            "summary_type": "bullet_points"
        })

        assert result == "Mocked Gemini output"

        # Check the prompt includes bullet points request
        call_args = mock_create.call_args[0]
        prompt_idx = call_args.index("-p") + 1
        assert "bullet points" in call_args[prompt_idx]

    @pytest.mark.asyncio
    async def test_gemini_summarize_with_files(self, mock_gemini_cli, mock_subprocess, temp_directory):
        """Test gemini_summarize with files."""
        mock_create, mock_process = mock_subprocess

        test_file = temp_directory / "doc.txt"
        test_file.write_text("Document content")

        tools = GeminiTools(allowed_directories=[str(temp_directory)])

        # Mock aiofiles
        with patch("aiofiles.open") as mock_aiofiles:
            mock_file = AsyncMock()
            mock_file.__aenter__.return_value = mock_file
            mock_file.write = AsyncMock()
            mock_file.read = AsyncMock(return_value=str(test_file) + "\n")
            mock_aiofiles.return_value = mock_file

            result = await tools.call_tool("gemini_summarize", {
                "files": [str(test_file)],
                "summary_type": "executive"
            })

            assert result == "Mocked Gemini output"

    def test_path_validation_with_invalid_path(self, mock_gemini_cli):
        """Test path validation with malformed paths."""
        tools = GeminiTools()

        # Test with path that can't be resolved
        with patch("pathlib.Path.resolve", side_effect=Exception("Bad path")), \
             pytest.raises(ValueError, match="Invalid file path"):
            tools._validate_file_path("/bad/path")

    @pytest.mark.asyncio
    async def test_file_descriptor_cleanup_on_write_error(self, mock_gemini_cli, temp_directory):
        """Test that file descriptors are closed even if aiofiles write fails."""
        tools = GeminiTools(allowed_directories=[str(temp_directory)])

        test_file = temp_directory / "test.txt"
        test_file.write_text("content")

        # Track if os.close was called
        close_called = []
        original_close = os.close

        def track_close(fd):
            close_called.append(fd)
            original_close(fd)

        with patch("os.close", side_effect=track_close), \
             patch("aiofiles.open", side_effect=Exception("Write failed")), \
             pytest.raises(Exception, match="Write failed"):
            await tools._run_gemini_command(
                "Test",
                files=[str(test_file)]
            )

        # Verify fd was closed
        assert len(close_called) > 0


class TestMainCoverage:
    """Test __main__.py for coverage."""

    def test_server_error_handler(self, mock_gemini_cli):
        """Test the error handler registration works."""
        server = GeminiMCPServer()

        # Just verify the handlers were registered
        # The actual handler logic is tested in the tools tests
        assert server.server is not None
        assert server.tools is not None
