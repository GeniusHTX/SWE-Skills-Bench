"""
Test for 'analyze-ci' skill — CI Failure Analysis
Validates that the Agent created a CI failure analysis script that
parses pytest log output, classifies failures, and reports results.
"""

import os
import re
import subprocess

import pytest


class TestAnalyzeCi:
    """Verify CI failure analysis script for sentry."""

    REPO_DIR = "/workspace/sentry"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    def _find_script(self):
        """Locate the CI analysis script in common paths."""
        candidates = [
            os.path.join(self.REPO_DIR, "scripts", "analyze_ci_failures.py"),
            os.path.join(self.REPO_DIR, "tools", "analyze_ci_failures.py"),
            os.path.join(self.REPO_DIR, "analyze_ci_failures.py"),
            os.path.join(self.REPO_DIR, "scripts", "analyze_ci.py"),
            os.path.join(self.REPO_DIR, "tools", "analyze_ci.py"),
            os.path.join(self.REPO_DIR, "analyze_ci.py"),
        ]
        for p in candidates:
            if os.path.isfile(p):
                return p
        # Fallback: search for it
        for root, _dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if "analyze" in f and "ci" in f and f.endswith(".py"):
                    return os.path.join(root, f)
        pytest.fail("CI analysis script not found in common locations")

    # ------------------------------------------------------------------
    # L1: File existence and syntax
    # ------------------------------------------------------------------

    def test_script_exists(self):
        """A CI failure analysis Python script must exist."""
        self._find_script()

    def test_script_compiles(self):
        """CI analysis script must be syntactically valid Python."""
        script = self._find_script()
        result = subprocess.run(
            ["python", "-m", "py_compile", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_has_main_entry(self):
        """Script must have a __main__ entry point or CLI interface."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        has_main = re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', content)
        has_argparse = "argparse" in content or "click" in content or "typer" in content
        assert (
            has_main or has_argparse
        ), "Script has no __main__ guard or CLI entry point"

    # ------------------------------------------------------------------
    # L1: Parsing capabilities
    # ------------------------------------------------------------------

    def test_parses_pytest_output(self):
        """Script must parse pytest-style log output."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"FAILED",
            r"ERROR",
            r"pytest",
            r"test.*fail",
            r"::.*::",
            r"short test summary",
            r"traceback",
        ]
        found = sum(1 for p in patterns if re.search(p, content, re.IGNORECASE))
        assert (
            found >= 2
        ), f"Only {found} pytest-related parsing pattern(s) — need at least 2"

    def test_extracts_test_name(self):
        """Script must extract test names from failures."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"test.name",
            r"test_name",
            r"node.id",
            r"nodeid",
            r"test.id",
            r"function.name",
            r"::\w+test",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not extract test names"

    def test_extracts_failure_message(self):
        """Script must extract failure messages."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"message",
            r"error.msg",
            r"reason",
            r"traceback",
            r"stderr",
            r"longrepr",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not extract failure messages"

    # ------------------------------------------------------------------
    # L2: Failure classification
    # ------------------------------------------------------------------

    def test_classifies_failure_types(self):
        """Script must categorize failures into types."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        categories = [
            r"assert",
            r"import",
            r"timeout",
            r"flak[ey]",
            r"type.error",
            r"value.error",
            r"runtime",
            r"connection",
            r"permission",
        ]
        found = sum(1 for p in categories if re.search(p, content, re.IGNORECASE))
        assert found >= 3, (
            f"Only {found} failure category(ies) detected — "
            "need at least 3 (e.g., assertion, import, timeout)"
        )

    def test_path_extraction(self):
        """Script must extract file paths from failures."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"file.?path",
            r"file_path",
            r"module",
            r"\.py",
            r"path",
            r"location",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not extract file paths from failures"

    # ------------------------------------------------------------------
    # L2: Output formats
    # ------------------------------------------------------------------

    def test_supports_text_output(self):
        """Script must support human-readable text output."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"print\(",
            r"format",
            r"table",
            r"report",
            r"stdout",
            r"text",
            r"summary",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not produce text output"

    def test_supports_json_output(self):
        """Script must support structured JSON output."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        assert "json" in content.lower(), "Script does not reference JSON output format"
        patterns = [
            r"json\.dump",
            r"json\.dumps",
            r"to_json",
            r"json_output",
            r"--json",
            r"format.*json",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not implement JSON serialization"

    def test_handles_empty_input(self):
        """Script should handle empty or no-failure input gracefully."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"no.*fail",
            r"empty",
            r"not.*found",
            r"len\(.*\)\s*==\s*0",
            r"if\s+not\s+",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not handle empty input case"

    def test_aggregation_summary(self):
        """Script should produce an aggregation summary of failures."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [r"summary", r"total", r"count", r"stats", r"aggregate", r"group"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not produce an aggregation summary"
