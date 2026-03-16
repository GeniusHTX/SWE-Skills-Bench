"""
Unit Test Runner - L2 functional-level tests
Runs unit tests and evaluates the pass rate.
"""

import re
from typing import Dict, Any, Optional, Tuple

from .base_evaluator import (
    BaseEvaluator,
    EvaluationLevel,
    EvaluationStatus,
    EvaluationResult,
)
from ..orchestrator.docker_manager import DockerManager
from ..orchestrator.logger import get_logger

logger = get_logger(__name__)


class UnitTestRunner(BaseEvaluator):
    """
    L2: Functional-level tests.

    Runs unit tests and evaluates the pass rate.
    """

    @property
    def level(self) -> EvaluationLevel:
        return EvaluationLevel.L2

    @property
    def method(self) -> str:
        return "unit_test"

    async def evaluate(self) -> EvaluationResult:
        """
        Run unit tests.

        Parameters:
            test_command: Test command (default: pytest)
            test_path: Path to test file/directory
            min_pass_rate: Minimum pass rate (0.0-1.0)
            working_dir: Working directory
            timeout: Timeout in seconds
        """
        logger.info("Running unit tests")

        test_command = self.params.get("test_command")
        test_path = self.params.get("test_path", "")
        min_pass_rate = self.params.get("min_pass_rate", 1.0)
        working_dir = self.params.get("working_dir", "/workspace")
        timeout = self.params.get("timeout", 600)

        # Build test command
        if not test_command:
            test_command = self._build_test_command(test_path)

        logger.info(f"Test command: {test_command}")
        logger.info(f"Working directory: {working_dir}")

        # Check whether test file exists in the container
        test_file_check_cmd = None
        if test_command and ".py" in test_command:
            # Extract test file path
            import re

            match = re.search(r"([/\w]+\.py)", test_command)
            if match:
                test_file_path = match.group(1)
                test_file_check_cmd = f"ls -la {test_file_path} 2>&1"
                check_result = self.docker_manager.execute_command(
                    test_file_check_cmd, timeout=10
                )
                logger.info(f"Test file check: {test_file_path}")
                logger.info(
                    f"Check result (exit={check_result.exit_code}): {check_result.stdout or check_result.stderr}"
                )

        # Run tests - explicitly set a non-source working directory to avoid import conflicts.
        # If test path is /tmp/benchmark_tests/, run from that directory instead of working_dir.
        # Also clear PYTHONPATH to avoid inheriting workspace paths.
        if "/tmp/benchmark_tests/" in test_command:
            # Run from the test file directory; clear PYTHONPATH to avoid importing workspace source
            cmd = f"cd /tmp/benchmark_tests && unset PYTHONPATH && {test_command}"
        else:
            cmd = f"cd {working_dir} && {test_command}"
        logger.info(f"Executing test command: {cmd}")

        result = self.docker_manager.execute_command(cmd, timeout=timeout)

        # Log raw output for debugging
        logger.debug(f"Test command exit code: {result.exit_code}")
        logger.debug(
            f"Test stdout length: {len(result.stdout) if result.stdout else 0}"
        )
        logger.debug(
            f"Test stderr length: {len(result.stderr) if result.stderr else 0}"
        )

        # Save raw test output to a temporary file for debugging
        try:
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix="_test_output.txt", encoding="utf-8"
            ) as f:
                f.write(f"Exit code: {result.exit_code}\n")
                f.write(f"{'='*60}\n")
                f.write(f"STDOUT:\n{result.stdout or ''}\n")
                f.write(f"{'='*60}\n")
                f.write(f"STDERR:\n{result.stderr or ''}\n")
                logger.info(f"Raw test output saved to: {f.name}")
        except Exception as e:
            logger.warning(f"Failed to save test output: {e}")

        # Check whether pytest is not installed (exclude false positives from non-existent cwd)
        if result.exit_code != 0:
            combined_output = (result.stdout or "") + "\n" + (result.stderr or "")
            lower_output = combined_output.lower()
            # If pytest started successfully (has 'collected' / 'test session starts' markers),
            # it is not considered uninstalled regardless of exit_code —
            # exit_code != 0 just means some tests failed.
            pytest_started = (
                "test session starts" in lower_output
                or "collected" in lower_output
                or "plugins:" in lower_output
            )
            # Only detect whether pytest is truly absent when it failed to start
            pytest_not_found = False
            if not pytest_started:
                pytest_not_found = (
                    "command not found" in lower_output
                    or "pytest: not found" in lower_output
                    or "no module named pytest" in lower_output
                    or (
                        "no such file or directory" in lower_output
                        and "pytest" in lower_output
                    )
                )
            if pytest_not_found:
                return self._create_result(
                    status=EvaluationStatus.ERROR,
                    score=0.0,
                    message="pytest is not installed in the container",
                    details={
                        "error": result.stderr[:1000] if result.stderr else "",
                        "stdout": result.stdout[:1000] if result.stdout else "",
                        "hint": "Make sure pytest is installed (python -m pip install pytest)",
                    },
                )

        # Parse test results
        test_results = self._parse_test_output(result.stdout, result.stderr)
        logger.debug(f"Parsed test results: {test_results}")

        if result.timed_out:
            return self._create_result(
                status=EvaluationStatus.FAILED,
                score=0.0,
                message="Test execution timed out",
                details={
                    "timeout": timeout,
                    "partial_output": result.stdout[:2000] if result.stdout else "",
                },
            )

        # Compute score
        total = test_results["total"]
        passed = test_results["passed"]

        if total == 0:
            return self._create_result(
                status=EvaluationStatus.SKIPPED,
                score=0.0,
                message="No tests found",
                details=test_results,
            )

        pass_rate = passed / total
        score = pass_rate

        # Determine pass/fail
        if pass_rate >= min_pass_rate:
            status = EvaluationStatus.PASSED
            message = f"Tests passed: {passed}/{total} ({pass_rate:.1%})"
        else:
            status = EvaluationStatus.FAILED
            message = f"Tests failed: {passed}/{total} ({pass_rate:.1%}), required {min_pass_rate:.1%}"

        return self._create_result(
            status=status,
            score=score,
            message=message,
            details={
                **test_results,
                "min_pass_rate": min_pass_rate,
                "actual_pass_rate": round(pass_rate, 3),
                "test_command": test_command,
                "duration": result.duration,
            },
        )

    def _build_test_command(self, test_path: str) -> str:
        """
        Build the test command.

        Uses 'python -m pytest' instead of the bare 'pytest' command to avoid
        issues in conda and similar environments where PATH may not be configured
        correctly and pytest cannot be found.
        """
        if test_path.endswith(".py"):
            return f"python -m pytest {test_path} -v --tb=short"
        elif test_path:
            return f"python -m pytest {test_path} -v --tb=short"
        else:
            return "python -m pytest -v --tb=short"

    def _parse_test_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """
        Parse test output.

        Supports:
        - pytest output
        - unittest output
        - generic test output
        """
        output = stdout + "\n" + stderr

        # Try parsing pytest output
        pytest_result = self._parse_pytest_output(output)
        if pytest_result["total"] > 0:
            return pytest_result

        # Try parsing unittest output
        unittest_result = self._parse_unittest_output(output)
        if unittest_result["total"] > 0:
            return unittest_result

        # Generic parsing
        return self._parse_generic_output(output)

    def _parse_pytest_output(self, output: str) -> Dict[str, Any]:
        """
        Parse pytest output.

        Note: ANSI escape sequences must be stripped before parsing.
        """
        result = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "failed_tests": [],
        }

        # Strip ANSI escape sequences (e.g. \x1b[1m)
        ansi_escape = re.compile(r"\x1b\[[0-9;]*[mGKH]")
        clean_output = ansi_escape.sub("", output)

        # ---- Extract the pytest summary line ----
        # The summary line looks like:
        #   "= 8 passed, 4 failed in 28.67s ="
        #   "==== 5 passed, 2 failed, 1 skipped, 38 errors in 1.23s ===="
        # We anchor to "in <number>s" followed by optional '=' to avoid
        # matching arbitrary "N errors" / "N passed" text inside test output.
        summary_line = ""
        summary_line_pattern = re.compile(
            r"^=.*\b\d+\s+(?:passed|failed|error|skipped).*\bin\s+[\d.]+s\b.*=*\s*$",
            re.MULTILINE,
        )
        summary_match = summary_line_pattern.search(clean_output)
        if summary_match:
            summary_line = summary_match.group(0)

        # Parse counts only from the summary line (not from full output)
        if summary_line:
            match = re.search(r"(\d+)\s+passed", summary_line)
            if match:
                result["passed"] = int(match.group(1))

            match = re.search(r"(\d+)\s+failed", summary_line)
            if match:
                result["failed"] = int(match.group(1))

            match = re.search(r"(\d+)\s+skipped", summary_line)
            if match:
                result["skipped"] = int(match.group(1))

            # Support both 'error' and 'errors'
            match = re.search(r"(\d+)\s+errors?", summary_line)
            if match:
                result["errors"] = int(match.group(1))

        # total includes all test types
        result["total"] = (
            result["passed"] + result["failed"] + result["skipped"] + result["errors"]
        )

        # Extract failed test names — only keep entries containing '::' (real test IDs)
        # to avoid capturing noise like '[' from progress indicators (e.g. "FAILED [100%]")
        failed_test_pattern = r"FAILED\s+(\S+::\S+)"
        result["failed_tests"] = re.findall(failed_test_pattern, clean_output)[:10]

        # Fallback: if summary line was not found (truncated output), count PASSED/FAILED per line
        if result["total"] == 0:
            passed_lines = len(re.findall(r"\bPASSED\b", clean_output))
            failed_lines = len(re.findall(r"\bFAILED\b", clean_output))
            if passed_lines > 0 or failed_lines > 0:
                result["passed"] = passed_lines
                result["failed"] = failed_lines
                result["total"] = passed_lines + failed_lines

        return result

    def _parse_unittest_output(self, output: str) -> Dict[str, Any]:
        """Parse unittest output."""
        result = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "failed_tests": [],
        }

        # Match unittest summary line
        # e.g. "Ran 10 tests in 0.123s"
        ran_pattern = r"Ran\s+(\d+)\s+test"
        match = re.search(ran_pattern, output)
        if match:
            result["total"] = int(match.group(1))

        # Check whether all tests passed
        if "OK" in output and result["total"] > 0:
            result["passed"] = result["total"]
        else:
            # Parse failure count
            failures_pattern = r"failures=(\d+)"
            match = re.search(failures_pattern, output)
            if match:
                result["failed"] = int(match.group(1))

            errors_pattern = r"errors=(\d+)"
            match = re.search(errors_pattern, output)
            if match:
                result["errors"] = int(match.group(1))

            result["passed"] = result["total"] - result["failed"] - result["errors"]

        return result

    def _parse_generic_output(self, output: str) -> Dict[str, Any]:
        """Generic test output parser."""
        result = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "failed_tests": [],
        }

        # Count PASS/FAIL occurrences
        result["passed"] = len(re.findall(r"\bPASS(?:ED)?\b", output, re.IGNORECASE))
        result["failed"] = len(re.findall(r"\bFAIL(?:ED)?\b", output, re.IGNORECASE))
        result["total"] = result["passed"] + result["failed"]

        return result


class MigrationApplyChecker(BaseEvaluator):
    """
    Database migration checker.

    Verifies that database migrations apply correctly.
    """

    @property
    def level(self) -> EvaluationLevel:
        return EvaluationLevel.L2

    @property
    def method(self) -> str:
        return "migration_apply"

    async def evaluate(self) -> EvaluationResult:
        """Run the migration check."""
        logger.info("Running migration check")

        command = self.params.get("command", "python manage.py migrate --check")
        working_dir = self.params.get("working_dir", "/workspace")

        cmd = f"cd {working_dir} && {command}"
        result = self.docker_manager.execute_command(cmd)

        if result.exit_code == 0:
            return self._create_result(
                status=EvaluationStatus.PASSED,
                score=1.0,
                message="Migration check passed",
            )
        else:
            return self._create_result(
                status=EvaluationStatus.FAILED,
                score=0.0,
                message="Migration check failed",
                details={
                    "output": result.stdout[:2000] if result.stdout else "",
                    "error": result.stderr[:2000] if result.stderr else "",
                },
            )
