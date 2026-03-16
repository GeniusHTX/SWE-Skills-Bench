"""
Degradation Handler - Code degradation processor
Removes specified code to simulate a "feature missing" state.
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..orchestrator.docker_manager import DockerManager
from ..orchestrator.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DegradationResult:
    """Degradation result."""

    file_path: str
    original_lines: int
    modified_lines: int
    removed_patterns: List[str]
    success: bool
    error: Optional[str] = None


class DegradationHandler:
    """
    Code degradation handler.

    Responsibilities:
    - Back up target files before modification
    - Run a custom script or built-in pattern removal against configured files
    - Simulate a "feature missing" state
    - Support multiple degradation strategies (pattern matching, AST manipulation, etc.)
    """

    def __init__(self, docker_manager: DockerManager, config: Dict[str, Any]):
        """
        Initialize.

        Args:
            docker_manager: Docker manager instance
            config: Global configuration
        """
        self.docker_manager = docker_manager
        self.config = config
        self.global_config = config.get("global", {})
        self.results: List[DegradationResult] = []

    async def run(self, pre_process_config: Dict[str, Any]) -> List[DegradationResult]:
        """
        Execute code degradation.

        Args:
            pre_process_config: Pre-processing configuration

        Returns:
            List[DegradationResult]: List of degradation results
        """
        logger.info("Starting code degradation")

        target_files = pre_process_config.get("target_files", [])
        params = pre_process_config.get("params", {})
        script_path = pre_process_config.get("script")

        # 1. Back up original files first
        await self._backup_files(target_files)

        # 2. If a custom script is provided, use it first
        if script_path:
            await self._run_degradation_script(script_path, target_files, params)
        else:
            # Fall back to built-in pattern-matching degradation
            await self._run_pattern_degradation(target_files, params)

        logger.info(f"Code degradation completed: {len(self.results)} files processed")
        return self.results

    async def _backup_files(self, target_files: List[str]):
        """Back up target files."""
        golden_dir = self.global_config.get(
            "golden_reference_dir", "/tmp/golden_reference"
        )
        workspace_dir = self.global_config.get("workspace_dir", "/workspace")

        logger.info(f"Backing up {len(target_files)} files to {golden_dir}")

        # Create backup root directory
        self.docker_manager.execute_command(f"mkdir -p {golden_dir}")

        for file_path in target_files:
            src = f"{workspace_dir}/{file_path}"

            # Create destination directory structure
            dst_dir = f"{golden_dir}/{'/'.join(file_path.split('/')[:-1])}"
            self.docker_manager.execute_command(f"mkdir -p {dst_dir}")

            # Copy file
            dst = f"{golden_dir}/{file_path}"
            result = self.docker_manager.execute_command(f"cp {src} {dst}")

            if result.exit_code == 0:
                logger.debug(f"Backed up: {file_path}")
            else:
                logger.warning(f"Failed to backup {file_path}: {result.stderr}")

    async def _run_degradation_script(
        self, script_path: str, target_files: List[str], params: Dict[str, Any]
    ):
        """Run a custom degradation script."""
        logger.info(f"Running degradation script: {script_path}")

        workspace_dir = self.global_config.get("workspace_dir", "/workspace")

        # Build script arguments
        files_arg = ",".join(target_files)
        patterns_arg = ",".join(params.get("remove_patterns", []))

        # Execute script
        cmd = (
            f"python {script_path} "
            f"--workspace {workspace_dir} "
            f"--files '{files_arg}' "
            f"--patterns '{patterns_arg}'"
        )

        result = self.docker_manager.execute_command(cmd)

        if result.exit_code != 0:
            logger.error(f"Degradation script failed: {result.stderr or result.stdout}")
            raise RuntimeError(
                f"Degradation script failed: {result.stderr or result.stdout}"
            )

        logger.info("Degradation script completed successfully")

    async def _run_pattern_degradation(
        self, target_files: List[str], params: Dict[str, Any]
    ):
        """Run pattern-based degradation."""
        logger.info("Running pattern-based degradation")

        workspace_dir = self.global_config.get("workspace_dir", "/workspace")
        remove_patterns = params.get("remove_patterns", [])

        if not remove_patterns:
            logger.warning("No patterns specified for degradation")
            return

        for file_path in target_files:
            full_path = f"{workspace_dir}/{file_path}"
            result = await self._degrade_file(full_path, remove_patterns)
            self.results.append(result)

    async def _degrade_file(
        self, file_path: str, patterns: List[str]
    ) -> DegradationResult:
        """
        Degrade a single file.

        Args:
            file_path: Path to the file
            patterns: List of patterns to remove

        Returns:
            DegradationResult: Degradation result
        """
        logger.debug(f"Degrading file: {file_path}")

        # Read file content
        result = self.docker_manager.execute_command(f"cat {file_path}")

        if result.exit_code != 0:
            return DegradationResult(
                file_path=file_path,
                original_lines=0,
                modified_lines=0,
                removed_patterns=[],
                success=False,
                error=f"Failed to read file: {result.stderr}",
            )

        content = result.stdout
        original_lines = len(content.split("\n"))
        removed_patterns = []

        # Apply each pattern
        for pattern in patterns:
            try:
                regex = re.compile(pattern, re.MULTILINE | re.DOTALL)
                if regex.search(content):
                    content = regex.sub("", content)
                    removed_patterns.append(pattern)
                    logger.debug(f"Removed pattern: {pattern}")
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")

        modified_lines = len(content.split("\n"))

        # Write content back to file
        # Write using heredoc
        write_result = self.docker_manager.execute_command(
            f"cat << 'DEGRADATION_EOF' > {file_path}\n{content}\nDEGRADATION_EOF"
        )

        if write_result.exit_code != 0:
            return DegradationResult(
                file_path=file_path,
                original_lines=original_lines,
                modified_lines=modified_lines,
                removed_patterns=removed_patterns,
                success=False,
                error=f"Failed to write file: {write_result.stderr}",
            )

        logger.info(
            f"Degraded {file_path}: "
            f"{original_lines} -> {modified_lines} lines, "
            f"{len(removed_patterns)} patterns removed"
        )

        return DegradationResult(
            file_path=file_path,
            original_lines=original_lines,
            modified_lines=modified_lines,
            removed_patterns=removed_patterns,
            success=True,
        )


class SmartDegradation:
    """
    Smart degradation handler.

    Provides more advanced degradation strategies:
    - Function-level removal
    - Code block removal
    - Comment-out replacement
    """

    @staticmethod
    def remove_function(content: str, function_name: str) -> str:
        """
        Remove a specified function.

        Args:
            content: File content
            function_name: Function name

        Returns:
            str: Modified content
        """
        # C/C++ function match pattern
        cpp_pattern = rf"^\s*\w+[\s\*]+{function_name}\s*\([^)]*\)\s*\{{[^}}]*\}}"

        # Python function match pattern
        py_pattern = rf"^def\s+{function_name}\s*\([^)]*\):[^\n]*\n(?:\s+[^\n]+\n)*"

        # Try both patterns
        content = re.sub(cpp_pattern, "", content, flags=re.MULTILINE | re.DOTALL)
        content = re.sub(py_pattern, "", content, flags=re.MULTILINE)

        return content

    @staticmethod
    def remove_case_block(content: str, case_value: str) -> str:
        """
        Remove a specific case from a switch statement.

        Args:
            content: File content
            case_value: Case value

        Returns:
            str: Modified content
        """
        pattern = rf"case\s+{case_value}:\s*[^;]*;(?:\s*break;)?"
        return re.sub(pattern, "", content, flags=re.MULTILINE | re.DOTALL)

    @staticmethod
    def comment_out_lines(content: str, pattern: str, comment_style: str = "//") -> str:
        """
        Comment out matching lines instead of deleting them.

        Args:
            content: File content
            pattern: Match pattern
            comment_style: Comment style

        Returns:
            str: Modified content
        """
        lines = content.split("\n")
        result_lines = []
        regex = re.compile(pattern)

        for line in lines:
            if regex.search(line):
                # Comment out the line
                result_lines.append(f"{comment_style} DEGRADED: {line}")
            else:
                result_lines.append(line)

        return "\n".join(result_lines)
