"""Tests for CLI commands."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from gemini_mcp.__main__ import cli


class TestCLI:
    """Test CLI commands."""

    def test_cli_default_runs_server(self, mock_gemini_cli):
        """Test that running without subcommand starts the server."""
        runner = CliRunner()

        with patch("gemini_mcp.__main__.GeminiMCPServer") as mock_server_class:
            mock_server = Mock()
            mock_server.run = Mock()
            mock_server_class.return_value = mock_server

            with patch("asyncio.run"):
                runner.invoke(cli, [])

                # Should create and try to run server
                mock_server_class.assert_called_once()

    def test_test_command_no_gemini(self):
        """Test the test command when Gemini is not installed."""
        runner = CliRunner()

        with patch("shutil.which", return_value=None):
            result = runner.invoke(cli, ["test"])

            assert result.exit_code == 0
            assert "Gemini CLI not found" in result.output

    def test_test_command_with_auth_error(self, mock_gemini_cli):
        """Test the test command with authentication error."""
        runner = CliRunner()

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: User not authenticated. Please run 'gemini auth login'"

        with patch("subprocess.run", return_value=mock_result):
            result = runner.invoke(cli, ["test"])

            assert result.exit_code == 0
            assert "not authenticated" in result.output
            assert "gemini auth login" in result.output

    def test_setup_command_all_good(self, mock_gemini_cli):
        """Test setup command when everything is configured."""
        runner = CliRunner()

        # Mock successful subprocess calls
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "gemini version 1.0.0"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = runner.invoke(cli, ["setup"])

            assert result.exit_code == 0
            assert "Everything looks good" in result.output

    def test_setup_command_auth_needed(self, mock_gemini_cli):
        """Test setup command when authentication is needed."""
        runner = CliRunner()

        # Mock version check success but auth failure
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "gemini version 1.0.0"

        auth_result = Mock()
        auth_result.returncode = 1
        auth_result.stderr = "Error: Not authenticated"

        def mock_run(cmd, **kwargs):
            if "--version" in cmd:
                return version_result
            else:
                return auth_result

        with patch("subprocess.run", side_effect=mock_run):
            result = runner.invoke(cli, ["setup"])

            assert result.exit_code == 0
            assert "Not authenticated" in result.output
            assert "gemini auth login" in result.output
            assert "Some issues need to be resolved" in result.output

    def test_list_tools_command(self, mock_gemini_cli):
        """Test list-tools command."""
        runner = CliRunner()

        result = runner.invoke(cli, ["list-tools"])

        assert result.exit_code == 0
        assert "gemini_prompt" in result.output
        assert "gemini_research" in result.output
        assert "gemini_analyze_code" in result.output
        assert "gemini_summarize" in result.output
