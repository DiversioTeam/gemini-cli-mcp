# Contributing to Gemini CLI MCP Server

Thank you for your interest in contributing to the Gemini CLI MCP Server! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to be respectful and constructive in all interactions.

## How to Contribute

### Reporting Issues

- Check if the issue already exists in the [issue tracker](https://github.com/DiversioTeam/gemini-cli-mcp/issues)
- Include clear reproduction steps
- Provide system information (OS, Python version, Gemini CLI version)
- Include relevant error messages and logs

### Suggesting Features

- Open an issue with the "enhancement" label
- Clearly describe the feature and its use case
- Be open to discussion about implementation approaches

### Submitting Code

1. **Fork the Repository**
   ```bash
   git clone https://github.com/DiversioTeam/gemini-cli-mcp.git
   cd gemini-cli-mcp
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set Up Development Environment**
   ```bash
   uv sync --all-extras --dev
   uv run pre-commit install
   ```

4. **Make Your Changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

5. **Run Tests and Quality Checks**
   ```bash
   # Run all tests
   uv run pytest

   # Check code style
   uv run ruff check .
   uv run ruff format .

   # Type checking
   uv run mypy src/

   # Security checks
   uv run ruff check --select S .
   ```

6. **Commit Your Changes**
   - Use clear, descriptive commit messages
   - Follow conventional commit format when possible:
     - `feat:` for new features
     - `fix:` for bug fixes
     - `docs:` for documentation changes
     - `test:` for test additions/changes
     - `refactor:` for code refactoring

7. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   - Open a pull request against the `main` branch
   - Fill out the PR template completely
   - Link any related issues

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all function parameters and returns
- Maximum line length: 100 characters
- Use meaningful variable and function names

### Testing

- Write tests for all new functionality
- Maintain or improve code coverage (minimum 80%)
- Use pytest fixtures for common test setup
- Test both success and failure cases

### Security

- Never commit secrets or credentials
- Validate all user inputs
- Follow the principle of least privilege
- Be mindful of file system access

### Documentation

- Update README.md for user-facing changes
- Add docstrings to all public functions and classes
- Include examples in docstrings where helpful
- Update type hints as code changes

## Review Process

1. All PRs require at least one review
2. CI checks must pass (tests, linting, type checking)
3. Code coverage must not decrease
4. Documentation must be updated if needed

## Release Process

Releases are managed by maintainers and follow semantic versioning:
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

## Questions?

Feel free to open an issue for any questions about contributing!
