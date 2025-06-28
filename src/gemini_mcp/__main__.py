"""Entry point for the Gemini MCP server."""

import asyncio
import logging
import sys

import click
from rich.console import Console
from rich.logging import RichHandler

from .server import GeminiMCPServer

console = Console()


def setup_logging(debug: bool = False) -> None:
    """Configure logging with rich output."""
    level = logging.DEBUG if debug else logging.INFO

    # When running as MCP server, redirect all logs to stderr
    stderr_console = Console(stderr=True)

    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=stderr_console, rich_tracebacks=True)],
    )


@click.group(invoke_without_command=True)
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx: click.Context, debug: bool) -> None:
    """Gemini MCP Server - AI research assistant via Gemini CLI."""
    setup_logging(debug)

    if ctx.invoked_subcommand is None:
        # Default behavior: run the server
        ctx.invoke(serve, debug=debug)


@cli.command()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def serve(debug: bool) -> None:
    """Run the MCP server."""
    stderr_console = Console(stderr=True)

    try:
        server = GeminiMCPServer()

        stderr_console.print("[green]Starting Gemini MCP Server...[/green]")
        asyncio.run(server.run())

    except RuntimeError as e:
        if "Gemini CLI not found" in str(e):
            stderr_console.print(f"[red]Error:[/red] {e}")
            stderr_console.print("\nPlease ensure Gemini CLI is installed and in your PATH.")
            stderr_console.print("You can check with: [cyan]which gemini[/cyan]")
        else:
            stderr_console.print(f"[red]Runtime error:[/red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        stderr_console.print("\n[yellow]Server stopped by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        stderr_console.print(f"[red]Unexpected error:[/red] {e}")
        if debug:
            stderr_console.print_exception()
        sys.exit(1)


@cli.command("test")
def test_gemini() -> None:
    """Test Gemini CLI installation and basic functionality."""
    import shutil
    import subprocess

    console.print("[bold]Gemini CLI Test[/bold]\n")

    # Check if Gemini is installed
    gemini_path = shutil.which("gemini")
    if not gemini_path:
        console.print("[red]✗ Gemini CLI not found in PATH[/red]")
        console.print("\nPlease install Gemini CLI first.")
        return

    console.print(f"[green]✓ Found Gemini CLI at:[/green] {gemini_path}")

    # Test basic functionality
    console.print("\n[yellow]Testing basic functionality...[/yellow]")
    try:
        result = subprocess.run(
            ["gemini", "-p", "Say 'Hello from Gemini MCP!'"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            console.print("[green]✓ Gemini CLI is working![/green]")
            console.print(f"\nResponse: {result.stdout.strip()}")
        else:
            console.print("[red]✗ Gemini CLI test failed[/red]")
            error_msg = result.stderr.strip()
            console.print(f"Error: {error_msg}")

            # Check for common authentication errors
            if any(phrase in error_msg.lower() for phrase in ["not authenticated", "login required", "auth", "credentials"]):
                console.print("\n[yellow]It looks like you're not authenticated.[/yellow]")
                console.print("Please run: [cyan]gemini auth login[/cyan]")
    except subprocess.TimeoutExpired:
        console.print("[red]✗ Gemini CLI test timed out[/red]")
    except Exception as e:
        console.print(f"[red]✗ Test failed:[/red] {e}")


@cli.command("list-tools")
def list_tools() -> None:
    """List all available MCP tools."""
    from .tools import GeminiTools

    console.print("[bold]Available Gemini MCP Tools[/bold]\n")

    try:
        tools = GeminiTools()
        for tool in tools.get_tool_definitions():
            console.print(f"[cyan]{tool.name}[/cyan]")
            console.print(f"  {tool.description}")
            console.print()
    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")


@cli.command("setup")
def setup_check() -> None:
    """Check Gemini CLI setup and provide guidance."""
    import os
    import shutil
    import subprocess

    console.print("[bold]Gemini MCP Setup Check[/bold]\n")

    all_good = True

    # 1. Check if Gemini CLI is installed
    console.print("[yellow]1. Checking Gemini CLI installation...[/yellow]")
    gemini_path = shutil.which("gemini")
    if not gemini_path:
        console.print("[red]✗ Gemini CLI not found[/red]")
        console.print("   Please install Gemini CLI and ensure it's in your PATH")
        console.print("   Installation guide: https://github.com/google/gemini-cli\n")
        all_good = False
    else:
        console.print(f"[green]✓ Found at: {gemini_path}[/green]\n")

        # 2. Check Gemini CLI version
        console.print("[yellow]2. Checking Gemini CLI version...[/yellow]")
        try:
            result = subprocess.run(
                ["gemini", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                console.print(f"[green]✓ Version: {result.stdout.strip()}[/green]\n")
            else:
                console.print("[red]✗ Could not get version[/red]\n")
        except Exception:
            console.print("[red]✗ Version check failed[/red]\n")

        # 3. Check authentication
        console.print("[yellow]3. Checking authentication...[/yellow]")
        try:
            result = subprocess.run(
                ["gemini", "-p", "Hello"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                console.print("[green]✓ Authentication working[/green]\n")
            else:
                error_msg = result.stderr.strip()
                if any(phrase in error_msg.lower() for phrase in ["not authenticated", "login required", "auth"]):
                    console.print("[red]✗ Not authenticated[/red]")
                    console.print("   Run: [cyan]gemini auth login[/cyan]\n")
                    all_good = False
                else:
                    console.print(f"[red]✗ Error: {error_msg}[/red]\n")
                    all_good = False
        except subprocess.TimeoutExpired:
            console.print("[red]✗ Authentication check timed out[/red]\n")
            all_good = False
        except Exception as e:
            console.print(f"[red]✗ Check failed: {e}[/red]\n")
            all_good = False

    # 4. Check environment
    console.print("[yellow]4. Checking environment...[/yellow]")
    allowed_dirs = os.environ.get("GEMINI_MCP_ALLOWED_DIRS")
    if allowed_dirs:
        console.print(f"[green]✓ Allowed directories: {allowed_dirs}[/green]")
    else:
        console.print("[cyan]i Using current directory for file access (default)[/cyan]")

    # Summary
    console.print("\n[bold]Summary:[/bold]")
    if all_good:
        console.print("[green]✓ Everything looks good! You're ready to use Gemini MCP.[/green]")
        console.print("\nRun the server with: [cyan]gemini-mcp[/cyan]")
    else:
        console.print("[red]✗ Some issues need to be resolved.[/red]")
        console.print("Please address the issues above and run setup again.")


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()

