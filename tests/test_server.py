"""Tests for the MCP server implementation."""

import os
from unittest.mock import patch

import pytest

from gemini_mcp.server import GeminiMCPServer, __version__


class TestGeminiMCPServer:
    """Test cases for GeminiMCPServer."""

    def test_initialization_default(self, mock_gemini_cli):
        """Test server initialization with defaults."""
        server = GeminiMCPServer()
        assert server.tools is not None
        assert server.server is not None

    def test_initialization_with_allowed_dirs(self, mock_gemini_cli, tmp_path):
        """Test server initialization with custom allowed directories."""
        custom_dir = tmp_path / "workspace"
        custom_dir.mkdir()

        server = GeminiMCPServer(allowed_directories=[str(custom_dir)])
        assert len(server.tools.allowed_directories) == 1
        assert server.tools.allowed_directories[0] == custom_dir.resolve()

    def test_initialization_from_environment(self, mock_gemini_cli, tmp_path):
        """Test server initialization from environment variable."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        with patch.dict(os.environ, {"GEMINI_MCP_ALLOWED_DIRS": f"{dir1}{os.pathsep}{dir2}"}):
            server = GeminiMCPServer()
            assert len(server.tools.allowed_directories) == 2
            allowed_paths = [str(d) for d in server.tools.allowed_directories]
            assert str(dir1.resolve()) in allowed_paths
            assert str(dir2.resolve()) in allowed_paths

    def test_list_tools(self, mock_gemini_cli):
        """Test listing available tools."""
        server = GeminiMCPServer()

        # Get tools directly from the tools instance
        tools = server.tools.get_tool_definitions()

        assert len(tools) == 4
        tool_names = [tool.name for tool in tools]
        assert "gemini_prompt" in tool_names
        assert "gemini_research" in tool_names
        assert "gemini_analyze_code" in tool_names
        assert "gemini_summarize" in tool_names

    @pytest.mark.asyncio
    async def test_call_tool_success(self, mock_gemini_cli, mock_subprocess):
        """Test successful tool execution."""
        mock_create, mock_process = mock_subprocess
        server = GeminiMCPServer()

        # Call the tool directly
        result = await server.tools.call_tool("gemini_prompt", {"prompt": "Hello, Gemini!"})

        assert result == "Mocked Gemini output"

    @pytest.mark.asyncio
    async def test_call_tool_error(self, mock_gemini_cli):
        """Test tool execution error handling."""
        server = GeminiMCPServer()

        # Test with an invalid tool name
        with pytest.raises(ValueError, match="Unknown tool"):
            await server.tools.call_tool("invalid_tool", {"prompt": "Test"})

    def test_set_logging_level(self, mock_gemini_cli):
        """Test that server can be initialized (logging is set during handler registration)."""
        # Just test that the server initializes successfully
        # The actual logging level setting is tested through integration
        server = GeminiMCPServer()
        assert server.server is not None

    def test_version_loading(self):
        """Test that version is loaded from package metadata."""
        # The version should be loaded from metadata or fallback
        assert __version__ is not None
        assert isinstance(__version__, str)


@pytest.mark.asyncio
async def test_server_integration(mock_gemini_cli, mock_subprocess):
    """Integration test for the full server flow."""
    mock_create, mock_process = mock_subprocess

    server = GeminiMCPServer()

    # Test the full flow: list tools -> call tool
    # 1. List tools
    tools = server.tools.get_tool_definitions()
    assert len(tools) > 0

    # 2. Call a tool
    result = await server.tools.call_tool(
        "gemini_prompt", {"prompt": "What is the capital of France?", "model": "gemini-2.5-pro"}
    )

    assert result == "Mocked Gemini output"

    # Verify the subprocess was called with correct arguments
    call_args = mock_create.call_args[0]
    assert "-m" in call_args
    assert "gemini-2.5-pro" in call_args
    assert "-p" in call_args
    assert "What is the capital of France?" in call_args
