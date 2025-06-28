# Gemini CLI MCP - Project Information

## Repository

- **GitHub**: https://github.com/DiversioTeam/gemini-cli-mcp
- **Organization**: DiversioTeam
- **License**: MIT

## Project Structure

```
gemini-cli-mcp/
├── src/
│   └── gemini_mcp/
│       ├── __init__.py      # Package initialization
│       ├── __main__.py      # CLI entry point with setup/test commands
│       ├── server.py        # MCP server implementation
│       └── tools.py         # Gemini CLI tool wrappers
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── test_cli.py          # CLI command tests
│   ├── test_coverage.py     # Additional coverage tests
│   ├── test_integration.py  # Integration and security tests
│   ├── test_server.py       # Server unit tests
│   └── test_tools.py        # Tools unit tests
├── .github/
│   └── workflows/
│       ├── ci.yml           # CI/CD pipeline
│       └── release.yml      # PyPI release automation
├── pyproject.toml           # Project configuration
├── README.md                # User documentation
├── CONTRIBUTING.md          # Contribution guidelines
├── LICENSE                  # MIT license
└── .pre-commit-config.yaml  # Pre-commit hooks
```

## Key Features

1. **Security**: Path validation, sandboxing, no shell injection
2. **Performance**: Full async implementation with aiofiles
3. **User Experience**: Setup diagnostics, clear error messages
4. **Quality**: 93% test coverage, type hints, linting
5. **CI/CD**: Multi-platform testing, automated releases

## Commands

- `gemini-mcp` - Run the MCP server
- `gemini-mcp setup` - Check installation and configuration
- `gemini-mcp test` - Test Gemini CLI functionality
- `gemini-mcp list-tools` - List available MCP tools

## Development

```bash
# Clone
git clone git@github.com:DiversioTeam/gemini-cli-mcp.git
cd gemini-cli-mcp

# Install
uv sync --all-extras --dev
uv run pre-commit install

# Test
uv run pytest

# Quality checks
uv run ruff check .
uv run mypy src/
```

## Publishing

The project is configured for automated PyPI releases via GitHub Actions.
Create a new release on GitHub to trigger the publication workflow.
