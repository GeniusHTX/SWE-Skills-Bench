"""
Build Checker - L1 build-level checks
Verifies that code passes compilation.
"""

from typing import Dict, Any

from .base_evaluator import (
    BaseEvaluator,
    EvaluationLevel,
    EvaluationStatus,
    EvaluationResult,
)
from ..orchestrator.docker_manager import DockerManager
from ..orchestrator.logger import get_logger

logger = get_logger(__name__)


class BuildChecker(BaseEvaluator):
    """
    L1: Build-level check.

    Evaluates whether code passes compilation / syntax checking.
    """

    @property
    def level(self) -> EvaluationLevel:
        return EvaluationLevel.L1

    @property
    def method(self) -> str:
        return "build_check"

    async def evaluate(self) -> EvaluationResult:
        """
        Run the build check.

        Parameters:
            build_command: Build command
            expected_exit_code: Expected exit code (default 0)
            working_dir: Working directory
        """
        logger.info("Running build check")

        build_command = self.params.get("build_command", "python -m py_compile *.py")
        expected_exit_code = self.params.get("expected_exit_code", 0)
        working_dir = self.params.get("working_dir", "/workspace")
        timeout = self.params.get("timeout", 600)  # Default 10 minutes

        # Execute build command
        cmd = f"cd {working_dir} && {build_command}"
        logger.debug(f"Executing: {cmd}")

        result = self.docker_manager.execute_command(cmd, timeout=timeout)

        # Analyze result
        if result.timed_out:
            return self._create_result(
                status=EvaluationStatus.FAILED,
                score=0.0,
                message="Build timed out",
                details={
                    "command": build_command,
                    "timeout": timeout,
                    "output": result.stdout[:2000] if result.stdout else "",
                },
            )

        if result.exit_code == expected_exit_code:
            return self._create_result(
                status=EvaluationStatus.PASSED,
                score=1.0,
                message="Build succeeded",
                details={
                    "command": build_command,
                    "exit_code": result.exit_code,
                    "duration": result.duration,
                },
            )
        else:
            # Extract error summary
            error_output = result.stderr or result.stdout
            error_summary = self._extract_error_summary(error_output)

            return self._create_result(
                status=EvaluationStatus.FAILED,
                score=0.0,
                message=f"Build failed with exit code {result.exit_code}",
                details={
                    "command": build_command,
                    "exit_code": result.exit_code,
                    "expected_exit_code": expected_exit_code,
                    "error_summary": error_summary,
                    "full_output": error_output[:5000] if error_output else "",
                },
            )

    def _extract_error_summary(self, output: str) -> str:
        """Extract an error summary from command output."""
        if not output:
            return "No error output"

        # Look for common error patterns
        error_lines = []

        for line in output.split("\n"):
            line_lower = line.lower()
            if any(
                keyword in line_lower
                for keyword in ["error:", "error[", "fatal:", "failed:", "undefined"]
            ):
                error_lines.append(line.strip())
                if len(error_lines) >= 5:
                    break

        if error_lines:
            return "\n".join(error_lines)

        # Return first few lines
        lines = output.strip().split("\n")
        return "\n".join(lines[:5])


class SyntaxChecker(BaseEvaluator):
    """
    Syntax checker.

    Checks for syntax errors only, without performing a full compilation.
    """

    @property
    def level(self) -> EvaluationLevel:
        return EvaluationLevel.L1

    @property
    def method(self) -> str:
        return "syntax_check"

    async def evaluate(self) -> EvaluationResult:
        """Run the syntax check."""
        logger.info("Running syntax check")

        target_files = self.params.get("target_files", [])
        language = self.params.get("language", "python")
        working_dir = self.params.get("working_dir", "/workspace")

        if not target_files:
            # If no files specified, check all relevant files
            target_files = await self._find_source_files(working_dir, language)

        errors = []
        checked_files = 0

        for file_path in target_files:
            check_result = await self._check_file_syntax(
                f"{working_dir}/{file_path}", language
            )
            checked_files += 1

            if check_result:
                errors.append({"file": file_path, "error": check_result})

        # Compute score
        if checked_files == 0:
            return self._create_result(
                status=EvaluationStatus.SKIPPED, score=1.0, message="No files to check"
            )

        error_rate = len(errors) / checked_files
        score = 1.0 - error_rate

        if errors:
            return self._create_result(
                status=EvaluationStatus.FAILED,
                score=score,
                message=f"Syntax errors found in {len(errors)} file(s)",
                details={
                    "checked_files": checked_files,
                    "files_with_errors": len(errors),
                    "errors": errors[:10],  # Limit error count
                },
            )
        else:
            return self._create_result(
                status=EvaluationStatus.PASSED,
                score=1.0,
                message=f"All {checked_files} files passed syntax check",
            )

    async def _find_source_files(self, working_dir: str, language: str) -> list:
        """Find source files matching the given language."""
        extensions = {
            "python": "*.py",
            "cpp": "*.cpp *.h *.hpp",
            "javascript": "*.js",
            "typescript": "*.ts",
        }

        pattern = extensions.get(language, "*.*")
        cmd = f"find {working_dir} -name '{pattern}' -type f | head -50"
        result = self.docker_manager.execute_command(cmd)

        if result.exit_code == 0:
            files = result.stdout.strip().split("\n")
            return [f.replace(working_dir + "/", "") for f in files if f]

        return []

    async def _check_file_syntax(self, file_path: str, language: str) -> str:
        """Check the syntax of a single file."""
        check_commands = {
            "python": f"python -m py_compile {file_path}",
            "cpp": f"g++ -fsyntax-only {file_path}",
            "javascript": f"node --check {file_path}",
        }

        cmd = check_commands.get(language)
        if not cmd:
            return ""

        result = self.docker_manager.execute_command(cmd)

        if result.exit_code != 0:
            return result.stderr or result.stdout or "Syntax error"

        return ""
