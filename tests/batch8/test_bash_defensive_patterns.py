"""
Test for 'bash-defensive-patterns' skill — Defensive Bash Scripting
Validates that the Agent created three defensive Bash scripts with strict mode,
atomic writes, trap cleanup, retry loops, and proper input validation.
"""

import os
import re
import subprocess

import pytest


class TestBashDefensivePatterns:
    """Verify defensive Bash scripting patterns in shellcheck repo."""

    REPO_DIR = "/workspace/shellcheck"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_download_script_exists(self):
        """Verify scripts/download-release.sh exists at expected path."""
        path = os.path.join(self.REPO_DIR, "scripts/download-release.sh")
        assert os.path.isfile(path), "scripts/download-release.sh missing"

    def test_pipeline_and_health_scripts_exist(self):
        """Verify scripts/run-pipeline.sh and scripts/health-check.sh exist."""
        for rel in ("scripts/run-pipeline.sh", "scripts/health-check.sh"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_scripts_executable(self):
        """Verify all three scripts are non-empty files."""
        for rel in ("scripts/download-release.sh", "scripts/run-pipeline.sh",
                     "scripts/health-check.sh"):
            path = os.path.join(self.REPO_DIR, rel)
            if not os.path.isfile(path):
                pytest.skip(f"{rel} does not exist")
            assert os.path.getsize(path) > 0, f"{rel} is empty"

    # ── semantic_check ──────────────────────────────────────────────

    def test_set_euo_pipefail_in_all_scripts(self):
        """Verify 'set -euo pipefail' strict mode appears in all three scripts."""
        for rel in ("scripts/download-release.sh", "scripts/run-pipeline.sh",
                     "scripts/health-check.sh"):
            content = self._read(os.path.join(self.REPO_DIR, rel))
            assert content, f"{rel} is empty or unreadable"
            assert "set -euo pipefail" in content, \
                f"'set -euo pipefail' not found in {rel}"

    def test_atomic_write_pattern_in_download_script(self):
        """Verify download-release.sh uses mktemp + mv atomic write pattern."""
        content = self._read(os.path.join(self.REPO_DIR, "scripts/download-release.sh"))
        assert content, "download-release.sh is empty or unreadable"
        assert "mktemp" in content, "mktemp not found in download-release.sh"
        assert "mv " in content, "mv (atomic move) not found in download-release.sh"

    def test_trap_err_cleanup_present(self):
        """Verify trap ERR or trap EXIT cleanup handler is present in download script."""
        content = self._read(os.path.join(self.REPO_DIR, "scripts/download-release.sh"))
        assert content, "download-release.sh is empty or unreadable"
        found = bool(re.search(r"trap.*ERR", content)) or bool(re.search(r"trap.*EXIT", content))
        assert found, "No trap ERR or trap EXIT handler found"

    def test_retry_loop_in_health_check(self):
        """Verify health-check.sh contains a retry loop with RETRY_COUNT variable."""
        content = self._read(os.path.join(self.REPO_DIR, "scripts/health-check.sh"))
        assert content, "health-check.sh is empty or unreadable"
        assert "RETRY_COUNT" in content, "RETRY_COUNT variable not found in health-check.sh"

    # ── functional_check (command) ──────────────────────────────────

    def _ensure_scripts_exist(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        script = os.path.join(self.REPO_DIR, "scripts/download-release.sh")
        if not os.path.isfile(script):
            pytest.skip("download-release.sh does not exist")

    def test_download_script_missing_url_exits_1(self):
        """Running download-release.sh with no arguments exits code 1."""
        self._ensure_scripts_exist()
        result = subprocess.run(
            ["bash", os.path.join(self.REPO_DIR, "scripts/download-release.sh")],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 1, f"Expected exit 1, got {result.returncode}"
        assert "Missing required argument" in result.stderr or "usage" in result.stderr.lower(), \
            "stderr missing usage/argument error message"

    def test_download_script_http_url_exits_1(self):
        """Running download-release.sh with http:// URL exits 1 with 'Invalid URL'."""
        self._ensure_scripts_exist()
        result = subprocess.run(
            ["bash", os.path.join(self.REPO_DIR, "scripts/download-release.sh"),
             "http://example.com/file.tar.gz"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 1, f"Expected exit 1, got {result.returncode}"
        assert "Invalid URL" in result.stderr or "https" in result.stderr.lower(), \
            "stderr missing 'Invalid URL' error"

    def test_log_output_contains_iso_timestamp(self):
        """Script stderr output contains ISO 8601 timestamp pattern."""
        self._ensure_scripts_exist()
        result = subprocess.run(
            ["bash", os.path.join(self.REPO_DIR, "scripts/download-release.sh")],
            capture_output=True, text=True, timeout=30,
        )
        pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
        assert re.search(pattern, result.stderr), \
            "No ISO 8601 timestamp found in stderr output"
