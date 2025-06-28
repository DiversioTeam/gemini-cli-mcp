"""Tool definitions for Gemini CLI integration."""

import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

import aiofiles
from mcp.types import Tool

logger = logging.getLogger(__name__)


# Default model constant to avoid repetition
DEFAULT_GEMINI_MODEL = "gemini-2.5-pro"


class GeminiTools:
    """Tools for interacting with Gemini CLI."""

    def __init__(self, allowed_directories: list[str] | None = None) -> None:
        """Initialize the tools.

        Args:
            allowed_directories: List of directories that files can be read from.
                                If None, defaults to current working directory.
        """
        gemini_path = shutil.which("gemini")
        if not gemini_path:
            raise RuntimeError("Gemini CLI not found in PATH")
        self.gemini_path: str = gemini_path
        logger.info(f"Found Gemini CLI at: {self.gemini_path}")

        # Security: Set allowed directories for file access
        if allowed_directories is None:
            self.allowed_directories = [Path.cwd()]
        else:
            self.allowed_directories = [Path(d).resolve() for d in allowed_directories]

        logger.info(f"Allowed directories: {[str(d) for d in self.allowed_directories]}")

    def get_tool_definitions(self) -> list[Tool]:
        """Get the list of available tools."""
        return [
            Tool(
                name="gemini_prompt",
                description="Send a prompt to Gemini CLI and get a response",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The prompt to send to Gemini",
                        },
                        "model": {
                            "type": "string",
                            "description": f"The model to use (default: {DEFAULT_GEMINI_MODEL})",
                            "default": DEFAULT_GEMINI_MODEL,
                        },
                        "context": {
                            "type": "string",
                            "description": "Additional context to prepend to the prompt",
                        },
                    },
                    "required": ["prompt"],
                },
            ),
            Tool(
                name="gemini_research",
                description="Use Gemini to research a topic with optional file context",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The research topic or question",
                        },
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of file paths to include as context",
                        },
                        "model": {
                            "type": "string",
                            "description": f"The model to use (default: {DEFAULT_GEMINI_MODEL})",
                            "default": DEFAULT_GEMINI_MODEL,
                        },
                    },
                    "required": ["topic"],
                },
            ),
            Tool(
                name="gemini_analyze_code",
                description="Use Gemini to analyze code files",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of code files to analyze",
                        },
                        "analysis_type": {
                            "type": "string",
                            "description": "Type of analysis to perform",
                            "enum": ["review", "explain", "optimize", "security", "test"],
                        },
                        "specific_question": {
                            "type": "string",
                            "description": "Specific question about the code",
                        },
                        "model": {
                            "type": "string",
                            "description": f"The model to use (default: {DEFAULT_GEMINI_MODEL})",
                            "default": DEFAULT_GEMINI_MODEL,
                        },
                    },
                    "required": ["files", "analysis_type"],
                },
            ),
            Tool(
                name="gemini_summarize",
                description="Use Gemini to summarize content from files or text",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Text content to summarize",
                        },
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Files to summarize (alternative to content)",
                        },
                        "summary_type": {
                            "type": "string",
                            "description": "Type of summary",
                            "enum": ["brief", "detailed", "bullet_points", "executive"],
                            "default": "brief",
                        },
                        "model": {
                            "type": "string",
                            "description": f"The model to use (default: {DEFAULT_GEMINI_MODEL})",
                            "default": DEFAULT_GEMINI_MODEL,
                        },
                    },
                    "required": [],
                },
            ),
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Call a specific tool."""
        if name == "gemini_prompt":
            return await self._gemini_prompt(arguments)
        elif name == "gemini_research":
            return await self._gemini_research(arguments)
        elif name == "gemini_analyze_code":
            return await self._gemini_analyze_code(arguments)
        elif name == "gemini_summarize":
            return await self._gemini_summarize(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    def _validate_file_path(self, file_path: str) -> Path:
        """Validate that a file path is within allowed directories.

        Args:
            file_path: Path to validate

        Returns:
            Resolved Path object

        Raises:
            ValueError: If path is outside allowed directories
        """
        # Resolve the path to handle .. and symlinks
        try:
            resolved_path = Path(file_path).resolve()
        except Exception as e:
            raise ValueError(f"Invalid file path: {file_path}") from e

        # Check if the resolved path is within any allowed directory
        for allowed_dir in self.allowed_directories:
            try:
                resolved_path.relative_to(allowed_dir)
                return resolved_path
            except ValueError:
                continue

        raise ValueError(
            f"File path '{file_path}' is outside allowed directories. "
            f"Allowed: {[str(d) for d in self.allowed_directories]}"
        )

    async def _run_gemini_command(
        self,
        prompt: str,
        model: str = DEFAULT_GEMINI_MODEL,
        files: list[str] | None = None,
        stdin_input: str | None = None,
    ) -> str:
        """Run a Gemini CLI command and return the output.

        Args:
            prompt: The prompt to send to Gemini
            model: The model to use
            files: Optional list of file paths to include
            stdin_input: Optional input to send via stdin

        Returns:
            Command output as string

        Raises:
            RuntimeError: If command execution fails
            ValueError: If file paths are invalid
        """
        cmd = [self.gemini_path, "-m", model, "-p", prompt]

        temp_file_list = None
        try:
            if files:
                # Validate all file paths first
                validated_paths = []
                for file_path in files:
                    validated_path = self._validate_file_path(file_path)
                    if not validated_path.exists():
                        raise ValueError(f"File does not exist: {file_path}")
                    validated_paths.append(str(validated_path))

                # Create a temporary file listing all files to include
                fd, temp_file_list = tempfile.mkstemp(suffix=".txt", text=True)
                try:
                    # Write file paths using regular file operations to ensure proper cleanup
                    with os.fdopen(fd, "w") as f:
                        for path in validated_paths:
                            f.write(f"{path}\n")

                    # Now fd is closed, safe to read the file
                    async with aiofiles.open(temp_file_list) as f:
                        file_list_content = await f.read()

                    # Add all files flag
                    cmd.append("-a")
                    stdin_input = stdin_input if stdin_input else file_list_content
                except Exception:
                    # fd is already closed by fdopen, no need to close it again
                    raise

            logger.debug(f"Running command: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate(
                input=stdin_input.encode() if stdin_input else None
            )

            if process.returncode != 0:
                error_msg = stderr.decode().strip()

                # Check for authentication errors
                if any(
                    phrase in error_msg.lower()
                    for phrase in ["not authenticated", "login required", "auth", "credentials"]
                ):
                    raise RuntimeError(
                        f"Gemini CLI authentication error: {error_msg}\n"
                        "Please run 'gemini auth login' to authenticate."
                    )

                raise RuntimeError(f"Gemini CLI error: {error_msg}")

            return stdout.decode().strip()

        finally:
            # Always clean up the temporary file
            if temp_file_list and os.path.exists(temp_file_list):
                try:
                    os.remove(temp_file_list)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary file {temp_file_list}: {e}")

    async def _gemini_prompt(self, arguments: dict[str, Any]) -> str:
        """Send a simple prompt to Gemini."""
        prompt = arguments["prompt"]
        model = arguments.get("model", DEFAULT_GEMINI_MODEL)
        context = arguments.get("context", "")

        full_prompt = f"{context}\n\n{prompt}" if context else prompt

        return await self._run_gemini_command(prompt=full_prompt, model=model)

    async def _gemini_research(self, arguments: dict[str, Any]) -> str:
        """Research a topic using Gemini."""
        topic = arguments["topic"]
        files = arguments.get("files", [])
        model = arguments.get("model", DEFAULT_GEMINI_MODEL)

        research_prompt = f"""Please research the following topic and provide a comprehensive analysis:

Topic: {topic}

Please include:
1. Overview and background
2. Key findings and insights
3. Relevant details and examples
4. Conclusions and recommendations

Be thorough but concise."""

        return await self._run_gemini_command(
            prompt=research_prompt,
            model=model,
            files=files,
        )

    async def _gemini_analyze_code(self, arguments: dict[str, Any]) -> str:
        """Analyze code using Gemini."""
        files = arguments["files"]
        analysis_type = arguments["analysis_type"]
        specific_question = arguments.get("specific_question", "")
        model = arguments.get("model", DEFAULT_GEMINI_MODEL)

        analysis_prompts = {
            "review": "Please review this code and identify potential issues, bugs, or areas for improvement.",
            "explain": "Please explain what this code does in detail, including its purpose and how it works.",
            "optimize": "Please suggest optimizations for this code to improve performance, readability, or maintainability.",
            "security": "Please analyze this code for security vulnerabilities and suggest fixes.",
            "test": "Please suggest test cases and testing strategies for this code.",
        }

        base_prompt = analysis_prompts.get(analysis_type, "Please analyze this code.")

        if specific_question:
            prompt = f"{base_prompt}\n\nSpecific question: {specific_question}"
        else:
            prompt = base_prompt

        return await self._run_gemini_command(
            prompt=prompt,
            model=model,
            files=files,
        )

    async def _gemini_summarize(self, arguments: dict[str, Any]) -> str:
        """Summarize content using Gemini."""
        content = arguments.get("content", "")
        files = arguments.get("files", [])
        summary_type = arguments.get("summary_type", "brief")
        model = arguments.get("model", DEFAULT_GEMINI_MODEL)

        if not content and not files:
            return "Error: Either content or files must be provided for summarization."

        summary_prompts = {
            "brief": "Please provide a brief summary of the following content in 2-3 sentences.",
            "detailed": "Please provide a detailed summary of the following content, covering all main points.",
            "bullet_points": "Please summarize the following content as bullet points.",
            "executive": "Please provide an executive summary of the following content suitable for decision makers.",
        }

        prompt = summary_prompts.get(summary_type, summary_prompts["brief"])

        if content:
            full_prompt = f"{prompt}\n\nContent:\n{content}"
            return await self._run_gemini_command(prompt=full_prompt, model=model)
        else:
            return await self._run_gemini_command(
                prompt=prompt,
                model=model,
                files=files,
            )
