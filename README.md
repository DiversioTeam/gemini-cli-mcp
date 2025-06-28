# Gemini CLI MCP Server

[![CI](https://github.com/DiversioTeam/gemini-cli-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/DiversioTeam/gemini-cli-mcp/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/DiversioTeam/gemini-cli-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/DiversioTeam/gemini-cli-mcp)
[![Python 3.10-3.13](https://img.shields.io/badge/python-3.10--3.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A Model Context Protocol (MCP) server that wraps the Gemini CLI, allowing AI assistants like Claude to use Gemini for research and analysis tasks.

> **Disclaimer**: This is an unofficial, community-developed tool that wraps the Google Gemini CLI. It is not affiliated with, endorsed by, or sponsored by Google. All Google and Gemini trademarks, service marks, and logos are the property of Google LLC. This project is licensed under the MIT License.

> **Important**: This tool requires that you have the Gemini CLI installed and authenticated on your system. See the [Prerequisites](#prerequisites) section for details.

## Features

- **gemini_prompt**: Send prompts to Gemini and get responses
- **gemini_research**: Research topics with optional file context
- **gemini_analyze_code**: Analyze code files for reviews, explanations, optimizations, security, or testing
- **gemini_summarize**: Summarize content from text or files

## Installation

### Using UV/UVX (Recommended)

```bash
# Install directly from the directory
uvx --from . gemini-mcp

# Or install in development mode
uv pip install -e .
```

### Using pip

```bash
pip install -e .
```

## Prerequisites

### 1. Python 3.10-3.13
Ensure you have Python 3.10, 3.11, 3.12, or 3.13 installed. The project is tested on all these versions.

### 2. Gemini CLI Installation and Authentication

This MCP server requires the Gemini CLI to be installed and authenticated:

1. **Install Gemini CLI**: Follow the official installation instructions for your platform
2. **Authenticate**: Run `gemini auth login` and follow the prompts
3. **Verify**: Test that it works by running `gemini -p "Hello, world!"`

If you see an authentication error, make sure you've completed the login process.

### 3. MCP-compatible Client
You'll need an MCP-compatible client such as:
- Claude Desktop
- Other MCP-compatible AI assistants

## Usage

### First Time Setup

Before running the server, verify your setup:

```bash
# Check if everything is configured correctly
gemini-mcp setup
```

This will check:
- Gemini CLI installation
- Authentication status
- Environment configuration

If you see authentication errors, run:
```bash
gemini auth login
```

### Running the Server

```bash
# Using UV/UVX
uvx --from . gemini-mcp

# Or if installed
gemini-mcp

# With debug logging
LOG_LEVEL=DEBUG gemini-mcp
```

### Configuring with Claude Desktop

Add this to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "gemini": {
      "command": "uvx",
      "args": ["--from", "/path/to/gemini-mcp", "gemini-mcp"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

Or if using Python directly:

```json
{
  "mcpServers": {
    "gemini": {
      "command": "python",
      "args": ["-m", "gemini_mcp"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Available Tools

### gemini_prompt
Send a simple prompt to Gemini.

**Parameters:**
- `prompt` (required): The prompt to send
- `model` (optional): The Gemini model to use (default: gemini-2.5-pro)
- `context` (optional): Additional context to prepend to the prompt

### gemini_research
Research a topic with optional file context.

**Parameters:**
- `topic` (required): The research topic or question
- `files` (optional): List of file paths to include as context
- `model` (optional): The Gemini model to use

### gemini_analyze_code
Analyze code files for various purposes.

**Parameters:**
- `files` (required): List of code files to analyze
- `analysis_type` (required): Type of analysis - one of:
  - `review`: Code review for issues and improvements
  - `explain`: Detailed explanation of the code
  - `optimize`: Performance and maintainability suggestions
  - `security`: Security vulnerability analysis
  - `test`: Test case suggestions
- `specific_question` (optional): Additional specific question
- `model` (optional): The Gemini model to use

### gemini_summarize
Summarize content from text or files.

**Parameters:**
- `content` (optional): Text content to summarize
- `files` (optional): Files to summarize (alternative to content)
- `summary_type` (optional): Type of summary - one of:
  - `brief`: 2-3 sentence summary (default)
  - `detailed`: Comprehensive summary
  - `bullet_points`: Bullet point format
  - `executive`: Executive summary for decision makers
- `model` (optional): The Gemini model to use

Note: Either `content` or `files` must be provided.

## Security

This MCP server implements several security measures:

### File Access Control
- **Sandboxed file access**: By default, file access is restricted to the current working directory
- **Path validation**: All file paths are validated to prevent directory traversal attacks
- **Configurable allowed directories**: You can specify allowed directories via:
  - Constructor parameter: `GeminiMCPServer(allowed_directories=["/path/to/safe/dir"])`
  - Environment variable: `GEMINI_MCP_ALLOWED_DIRS=/path1:/path2:/path3`

### Input Sanitization
- All user inputs are properly sanitized before being passed to the CLI
- Command injection is prevented by using subprocess with argument lists (never shell=True)
- File paths are resolved and validated before use

### Best Practices
- Always run the server with minimal required permissions
- Regularly update both the MCP server and Gemini CLI
- Monitor logs for any suspicious activity

## Development

### Setting up the Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/DiversioTeam/gemini-cli-mcp.git
   cd gemini-cli-mcp
   ```

2. Install development dependencies:
   ```bash
   uv sync --all-extras --dev
   ```

3. Install pre-commit hooks:
   ```bash
   uv run pre-commit install
   ```

### Running Tests

```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/test_tools.py

# Run with verbose output
uv run pytest -v
```

### Code Quality

```bash
# Run linting
uv run ruff check .

# Run formatting
uv run ruff format .

# Run type checking
uv run mypy src/

# Run security checks
uv run bandit -r src/
```

## Troubleshooting

### Quick Diagnostics

Run the setup check to diagnose common issues:
```bash
gemini-mcp setup
```

### Common Issues

1. **"Gemini CLI not found in PATH"**
   - Ensure Gemini CLI is installed: `which gemini`
   - Add Gemini to your PATH if needed
   - Follow the installation guide for your platform

2. **Authentication errors**
   - The server will detect if you're not authenticated
   - Run `gemini auth login` to authenticate
   - Check if your credentials have expired
   - The error message will guide you on what to do

3. **File access errors**
   - Check that files are within allowed directories
   - Use absolute paths or ensure relative paths are correct
   - Set `GEMINI_MCP_ALLOWED_DIRS` for custom directories

4. **"Command not found" errors**
   - Run `gemini-mcp setup` to check your installation
   - Ensure you've installed the package: `uv pip install -e .`

### Debug Logging

Enable debug logging to see detailed information:

```bash
LOG_LEVEL=DEBUG gemini-mcp
```

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Ensure all tests pass and code quality checks succeed
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on top of the [Model Context Protocol](https://github.com/anthropics/mcp)
- Integrates with Google's Gemini CLI (unofficial integration)
- Inspired by the MCP ecosystem and community