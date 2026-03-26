"""
Test for 'analyze-ci' skill — CI Failure Analyzer
Validates that the Agent created a CI failure analysis script that parses pytest
output logs and generates structured JSON diagnostic reports.
"""

import os
import json
import subprocess
import pytest


class TestAnalyzeCi:
    """Verify CI failure analysis script for Sentry."""

    REPO_DIR = "/workspace/sentry"

    # ------------------------------------------------------------------
    # L1: file existence & syntax
    # ------------------------------------------------------------------

    def test_analysis_script_exists(self):
        """scripts/analyze_ci_failures.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "scripts", "analyze_ci_failures.py")
        assert os.path.isfile(fpath), "analyze_ci_failures.py not found"

    def test_sample_log_exists(self):
        """sample_pytest_output.log must exist."""
        candidates = [
            os.path.join(self.REPO_DIR, "sample_pytest_output.log"),
            os.path.join(self.REPO_DIR, "scripts", "sample_pytest_output.log"),
        ]
        found = any(os.path.isfile(c) for c in candidates)
        assert found, f"sample_pytest_output.log not found at {candidates}"

    def test_script_compiles(self):
        """Analysis script must compile without syntax errors."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "scripts/analyze_ci_failures.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: functional verification
    # ------------------------------------------------------------------

    def _find_sample_log(self):
        for p in ["sample_pytest_output.log", "scripts/sample_pytest_output.log"]:
            fpath = os.path.join(self.REPO_DIR, p)
            if os.path.isfile(fpath):
                return p
        pytest.fail("sample_pytest_output.log not found")

    def test_script_runs_with_input(self):
        """Script must run with --input/--output and exit code 0."""
        log_path = self._find_sample_log()
        result = subprocess.run(
            [
                "python",
                "scripts/analyze_ci_failures.py",
                "--input",
                log_path,
                "--output",
                "/tmp/ci_report.json",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert (
            result.returncode == 0
        ), f"Script failed (rc={result.returncode}):\n{result.stderr}"

    def test_output_json_is_valid(self):
        """Output report must be valid JSON."""
        log_path = self._find_sample_log()
        subprocess.run(
            [
                "python",
                "scripts/analyze_ci_failures.py",
                "--input",
                log_path,
                "--output",
                "/tmp/ci_report.json",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert os.path.isfile("/tmp/ci_report.json"), "Report not generated"
        with open("/tmp/ci_report.json", "r") as f:
            data = json.load(f)
        assert isinstance(data, dict), "Report root must be a JSON object"

    def test_output_has_failed_tests_field(self):
        """Report must contain failed_tests field."""
        log_path = self._find_sample_log()
        subprocess.run(
            [
                "python",
                "scripts/analyze_ci_failures.py",
                "--input",
                log_path,
                "--output",
                "/tmp/ci_report.json",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        with open("/tmp/ci_report.json", "r") as f:
            data = json.load(f)
        assert (
            "failed_tests" in data
        ), f"Missing failed_tests; keys: {list(data.keys())}"
        assert isinstance(data["failed_tests"], list), "failed_tests must be a list"

    def test_output_has_error_type_field(self):
        """Report must contain error_type field."""
        log_path = self._find_sample_log()
        subprocess.run(
            [
                "python",
                "scripts/analyze_ci_failures.py",
                "--input",
                log_path,
                "--output",
                "/tmp/ci_report.json",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        with open("/tmp/ci_report.json", "r") as f:
            data = json.load(f)
        assert "error_type" in data, f"Missing error_type; keys: {list(data.keys())}"

    def test_output_has_stack_summary_field(self):
        """Report must contain stack_summary field."""
        log_path = self._find_sample_log()
        subprocess.run(
            [
                "python",
                "scripts/analyze_ci_failures.py",
                "--input",
                log_path,
                "--output",
                "/tmp/ci_report.json",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        with open("/tmp/ci_report.json", "r") as f:
            data = json.load(f)
        assert (
            "stack_summary" in data
        ), f"Missing stack_summary; keys: {list(data.keys())}"

    def test_failed_tests_not_empty(self):
        """Sample log contains failures, so failed_tests should not be empty."""
        log_path = self._find_sample_log()
        subprocess.run(
            [
                "python",
                "scripts/analyze_ci_failures.py",
                "--input",
                log_path,
                "--output",
                "/tmp/ci_report.json",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        with open("/tmp/ci_report.json", "r") as f:
            data = json.load(f)
        assert (
            len(data.get("failed_tests", [])) >= 1
        ), "failed_tests is empty; sample log should contain at least 1 failure"

    def test_sample_log_has_valid_format(self):
        """Sample log must contain pytest-style output markers."""
        log_path = self._find_sample_log()
        fpath = os.path.join(self.REPO_DIR, log_path)
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        markers = ["FAILED", "PASSED", "ERROR", "=====", "-----"]
        found = sum(1 for m in markers if m in content)
        assert (
            found >= 2
        ), f"Sample log doesn't look like pytest output (matched {found} markers)"

    def test_cli_help_available(self):
        """Script --help should work."""
        result = subprocess.run(
            ["python", "scripts/analyze_ci_failures.py", "--help"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"--help failed:\n{result.stderr}"
        assert "--input" in result.stdout, "--input not mentioned in help"
