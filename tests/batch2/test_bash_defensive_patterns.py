"""
Test for 'bash-defensive-patterns' skill — Defensive Bash Scripts
Validates that the Agent created defensive Bash script examples with
error handling, safe variable usage, input validation, and ShellCheck compliance.
"""

import os
import re
import stat
import subprocess

import pytest


class TestBashDefensivePatterns:
    """Verify defensive Bash script examples for ShellCheck."""

    REPO_DIR = "/workspace/shellcheck"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_defensive_example_exists(self):
        """test/defensive_example.sh must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "test", "defensive_example.sh")
        )

    def test_safe_io_exists(self):
        """test/safe_io.sh must exist."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, "test", "safe_io.sh"))

    # ------------------------------------------------------------------
    # L1: Scripts are executable
    # ------------------------------------------------------------------

    def test_defensive_example_executable(self):
        """defensive_example.sh should be executable."""
        path = os.path.join(self.REPO_DIR, "test", "defensive_example.sh")
        mode = os.stat(path).st_mode
        assert mode & (
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        ), "defensive_example.sh is not executable"

    def test_safe_io_executable(self):
        """safe_io.sh should be executable."""
        path = os.path.join(self.REPO_DIR, "test", "safe_io.sh")
        mode = os.stat(path).st_mode
        assert mode & (
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        ), "safe_io.sh is not executable"

    # ------------------------------------------------------------------
    # L2: Error handling
    # ------------------------------------------------------------------

    def test_defensive_uses_strict_mode(self):
        """defensive_example.sh must use set -euo pipefail."""
        content = self._read("test", "defensive_example.sh")
        assert re.search(
            r"set\s+-euo\s+pipefail", content
        ), "Missing 'set -euo pipefail'"

    def test_safe_io_uses_strict_mode(self):
        """safe_io.sh must use set -euo pipefail."""
        content = self._read("test", "safe_io.sh")
        assert re.search(
            r"set\s+-euo\s+pipefail", content
        ), "Missing 'set -euo pipefail'"

    def test_trap_based_cleanup(self):
        """At least one script must use trap for cleanup."""
        combined = self._read("test", "defensive_example.sh") + self._read(
            "test", "safe_io.sh"
        )
        assert re.search(r"trap\s+", combined), "No trap-based cleanup found"

    def test_shebang_line(self):
        """Scripts should have proper shebang line."""
        for script in ("defensive_example.sh", "safe_io.sh"):
            content = self._read("test", script)
            assert content.startswith("#!"), f"{script} missing shebang line"

    # ------------------------------------------------------------------
    # L2: Safe variable usage
    # ------------------------------------------------------------------

    def test_quoted_variables(self):
        """Scripts must quote variable expansions."""
        for script in ("defensive_example.sh", "safe_io.sh"):
            content = self._read("test", script)
            # Should have quoted "$var" patterns
            assert re.search(
                r'".*\$\w+.*"', content
            ), f"{script} has unquoted variable expansions"

    def test_default_values(self):
        """Scripts should use ${var:-default} for fallback values."""
        combined = self._read("test", "defensive_example.sh") + self._read(
            "test", "safe_io.sh"
        )
        assert re.search(
            r"\$\{[^}]+:-", combined
        ), "No ${var:-default} fallback patterns found"

    # ------------------------------------------------------------------
    # L2: Input validation
    # ------------------------------------------------------------------

    def test_argument_validation(self):
        """safe_io.sh must validate command-line arguments."""
        content = self._read("test", "safe_io.sh")
        patterns = [
            r"\$#",
            r"argc",
            r"if\s+\[.*-z",
            r"if\s+\[.*-lt",
            r"usage\(\)",
            r"print_usage",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "safe_io.sh does not validate arguments"

    def test_path_sanitization(self):
        """safe_io.sh must sanitize file paths."""
        content = self._read("test", "safe_io.sh")
        patterns = [
            r"realpath",
            r"readlink",
            r"basename",
            r"\.\./",
            r"sanitiz",
            r"canonicalize",
            r"dirname",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "safe_io.sh does not sanitize paths"

    def test_file_existence_checks(self):
        """Scripts must check file existence before operations."""
        combined = self._read("test", "defensive_example.sh") + self._read(
            "test", "safe_io.sh"
        )
        patterns = [r"-f\s+", r"-d\s+", r"-e\s+", r"-r\s+", r"test\s+"]
        assert any(
            re.search(p, combined) for p in patterns
        ), "No file existence checks found"

    # ------------------------------------------------------------------
    # L2: ShellCheck compliance
    # ------------------------------------------------------------------

    def test_shellcheck_defensive_example(self):
        """defensive_example.sh must pass shellcheck."""
        result = subprocess.run(
            ["shellcheck", "--severity=warning", "test/defensive_example.sh"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"ShellCheck warnings:\n{result.stdout}"

    def test_shellcheck_safe_io(self):
        """safe_io.sh must pass shellcheck."""
        result = subprocess.run(
            ["shellcheck", "--severity=warning", "test/safe_io.sh"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"ShellCheck warnings:\n{result.stdout}"
