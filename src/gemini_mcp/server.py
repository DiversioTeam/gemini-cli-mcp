"""MCP server implementation for Gemini CLI integration."""

import logging
import os
from importlib import metadata
from logging import CRITICAL as LOG_CRITICAL
from logging import DEBUG as LOG_DEBUG
from logging import ERROR as LOG_ERROR
from logging import INFO as LOG_INFO
from logging import WARNING as LOG_WARNING
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.lowlevel import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    EmbeddedResource,
    ImageContent,
    LoggingLevel,
    TextContent,
    Tool,
)

from .tools import GeminiTools

logger = logging.getLogger(__name__)

# Get version from package metadata
try:
    __version__ = metadata.version("gemini-mcp")
except Exception:
    __version__ = "0.1.0"  # Fallback version


class GeminiMCPServer:
    """MCP Server for Gemini CLI integration."""

    def __init__(self, allowed_directories: list[str] | None = None) -> None:
        """Initialize the server.

        Args:
            allowed_directories: List of directories that files can be read from.
                                If None, defaults to current working directory.
        """
        # Initialize allowed directories from environment or parameter
        if allowed_directories is None:
            # Check for environment variable
            env_dirs = os.environ.get("GEMINI_MCP_ALLOWED_DIRS")
            if env_dirs:
                # Use os.pathsep for platform-specific path separator
                allowed_directories = [d.strip() for d in env_dirs.split(os.pathsep) if d.strip()]
            else:
                # Default to current working directory
                allowed_directories = [str(Path.cwd())]

        self.tools = GeminiTools(allowed_directories=allowed_directories)
        self.server: Server = Server("gemini-mcp")

        # Register handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all MCP handlers."""

        @self.server.list_tools()  # type: ignore[misc]
        async def list_tools() -> list[Tool]:
            """List all available tools."""
            return self.tools.get_tool_definitions()

        @self.server.call_tool()  # type: ignore[misc]
        async def call_tool(
            name: str, arguments: dict[str, Any] | None = None
        ) -> list[TextContent | ImageContent | EmbeddedResource]:
            """Call a specific tool."""
            logger.debug(f"Calling tool: {name} with arguments: {arguments}")

            try:
                result = await self.tools.call_tool(name, arguments or {})
                return [TextContent(type="text", text=result)]
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}", exc_info=True)
                return [TextContent(type="text", text=f"Error: {e!s}")]

        @self.server.set_logging_level()  # type: ignore[misc]
        async def set_logging_level(level: LoggingLevel) -> None:
            """Set the logging level."""
            logger.info(f"Setting logging level to: {level}")
            level_map: dict[str, int] = {
                "debug": LOG_DEBUG,
                "info": LOG_INFO,
                "notice": LOG_INFO,  # Python logging doesn't have NOTICE, map to INFO
                "warning": LOG_WARNING,
                "error": LOG_ERROR,
                "critical": LOG_CRITICAL,
                "alert": LOG_CRITICAL,  # Python logging doesn't have ALERT, map to CRITICAL
                "emergency": LOG_CRITICAL,  # Python logging doesn't have EMERGENCY, map to CRITICAL
            }
            logging.getLogger().setLevel(level_map.get(level, LOG_INFO))

    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting Gemini MCP Server")
        logger.info(f"Version: {__version__}")
        logger.info(f"Gemini CLI: {self.tools.gemini_path}")
        logger.info(f"Allowed directories: {[str(d) for d in self.tools.allowed_directories]}")

        # Run the stdio server
        async with stdio_server() as (read_stream, write_stream):
            init_options = InitializationOptions(
                server_name="gemini-mcp",
                server_version=__version__,
                capabilities=self.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            )

            await self.server.run(
                read_stream,
                write_stream,
                init_options,
            )
