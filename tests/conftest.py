"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_gemini_cli():
    """Mock the gemini CLI being available."""
    with patch("shutil.which") as mock_which:
        mock_which.return_value = "/usr/local/bin/gemini"
        yield mock_which


@pytest.fixture
def temp_directory(tmp_path):
    """Create a temporary directory for testing file operations."""
    # Create some test files
    (tmp_path / "test1.txt").write_text("Test content 1")
    (tmp_path / "test2.py").write_text("print('Hello, World!')")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "test3.md").write_text("# Test Markdown")

    return tmp_path


@pytest.fixture
async def mock_subprocess():
    """Mock asyncio subprocess for testing command execution."""
    with patch("asyncio.create_subprocess_exec") as mock_create:
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (
            b"Mocked Gemini output",
            b"",  # stderr
        )
        mock_create.return_value = mock_process
        yield mock_create, mock_process


@pytest.fixture
def sample_tool_arguments():
    """Sample arguments for different tools."""
    return {
        "gemini_prompt": {"prompt": "What is the meaning of life?", "model": "gemini-2.5-pro"},
        "gemini_research": {
            "topic": "Python asyncio best practices",
            "files": ["test1.txt", "test2.py"],
            "model": "gemini-2.5-pro",
        },
        "gemini_analyze_code": {
            "files": ["test2.py"],
            "analysis_type": "review",
            "specific_question": "Is this code secure?",
            "model": "gemini-2.5-pro",
        },
        "gemini_summarize": {
            "content": "This is a long text that needs summarization...",
            "summary_type": "brief",
            "model": "gemini-2.5-pro",
        },
    }


@pytest.fixture
def mock_server_streams():
    """Mock the stdio streams for server testing."""
    read_stream = AsyncMock()
    write_stream = AsyncMock()

    # Mock the read stream to simulate client requests
    read_stream.read.side_effect = [
        # Simulate initialization
        b'{"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1}',
        # Simulate tool list request
        b'{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2}',
        # Simulate shutdown
        b'{"jsonrpc": "2.0", "method": "shutdown", "params": {}, "id": 3}',
    ]

    return read_stream, write_stream
