"""
Test for 'bash-defensive-patterns' skill — ShellCheck Defensive Bash Scripts
Validates shell scripts with set -euo pipefail, structured logging,
retry/lock helpers, sourcing patterns, and shellcheck compliance.
"""

import os
import re
import subprocess

import pytest


class TestBashDefensivePatterns:
    """Verify defensive Bash scripting patterns."""

    REPO_DIR = "/workspace/shellcheck"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_shell_scripts_exist(self):
        """Verify at least 3 shell scripts exist in the repo."""
        sh_files = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".sh") or f.endswith(".bash"):
                    sh_files.append(os.path.join(dirpath, f))
        assert len(sh_files) >= 3, f"Expected ≥3 shell scripts, found {len(sh_files)}"

    def test_deploy_script_exists(self):
        """Verify a deploy or main entry script exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".sh") and (
                    "deploy" in f.lower() or "main" in f.lower() or "run" in f.lower()
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No deploy/main shell script found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_set_euo_pipefail(self):
        """Verify at least one script uses set -euo pipefail."""
        sh_files = self._find_sh_files()
        assert sh_files, "No shell scripts found"
        for fpath in sh_files:
            content = self._read(fpath)
            if re.search(r"set\s+-[euo]+\s*pipefail|set\s+-euo\s+pipefail", content):
                return
            if (
                "set -e" in content
                and "set -u" in content
                and "set -o pipefail" in content
            ):
                return
        pytest.fail("No script uses 'set -euo pipefail'")

    def test_log_functions_defined(self):
        """Verify structured logging functions (log_info, log_warn, log_error)."""
        sh_files = self._find_sh_files()
        assert sh_files, "No shell scripts found"
        log_funcs = set()
        for fpath in sh_files:
            content = self._read(fpath)
            for func in ["log_info", "log_warn", "log_error"]:
                if re.search(rf"(function\s+{func}|{func}\s*\(\s*\))", content):
                    log_funcs.add(func)
        assert len(log_funcs) >= 2, f"Expected ≥2 log functions, found: {log_funcs}"

    def test_retry_or_lock_helper(self):
        """Verify retry and/or lock acquisition helper exists."""
        sh_files = self._find_sh_files()
        assert sh_files, "No shell scripts found"
        for fpath in sh_files:
            content = self._read(fpath)
            if re.search(r"(retry|acquire_lock|with_lock|flock)", content):
                return
        pytest.fail("No retry or lock helper found")

    def test_deploy_sources_common(self):
        """Verify deploy script sources a common/shared library."""
        sh_files = self._find_sh_files()
        for fpath in sh_files:
            if "deploy" in os.path.basename(fpath).lower():
                content = self._read(fpath)
                if re.search(r"(source|\.)\s+.*(common|lib|shared|utils)", content):
                    return
        # Check any script sources another
        for fpath in sh_files:
            content = self._read(fpath)
            if re.search(r"(source|\.)\s+.*\.sh", content):
                return
        pytest.fail("No script sources a common/shared library")

    def test_iso_timestamp_in_logs(self):
        """Verify logging uses ISO 8601 timestamp format."""
        sh_files = self._find_sh_files()
        assert sh_files, "No shell scripts found"
        for fpath in sh_files:
            content = self._read(fpath)
            if re.search(
                r"date.*\+.*%Y.*%m.*%d|%FT%T|iso.?8601|--iso", content, re.IGNORECASE
            ):
                return
            if re.search(r'"\$\(date\b', content):
                return
        pytest.fail("No ISO timestamp in logging functions")

    # ── functional_check ────────────────────────────────────────────────────

    def test_shellcheck_compliance(self):
        """Verify scripts pass ShellCheck (if available)."""
        sh_files = self._find_sh_files()
        assert sh_files, "No shell scripts found"
        try:
            subprocess.run(["shellcheck", "--version"], capture_output=True, timeout=10)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("shellcheck not available")
        errors = []
        for fpath in sh_files[:5]:  # Check up to 5 scripts
            result = subprocess.run(
                ["shellcheck", "-S", "error", fpath],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                errors.append(os.path.basename(fpath))
        assert not errors, f"ShellCheck errors in: {errors}"

    def test_bash_syntax_valid(self):
        """Verify scripts pass bash -n syntax check."""
        sh_files = self._find_sh_files()
        assert sh_files, "No shell scripts found"
        try:
            subprocess.run(["bash", "--version"], capture_output=True, timeout=10)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("bash not available")
        for fpath in sh_files[:5]:
            result = subprocess.run(
                ["bash", "-n", fpath], capture_output=True, text=True, timeout=30
            )
            assert (
                result.returncode == 0
            ), f"Syntax error in {os.path.basename(fpath)}: {result.stderr}"

    def test_retry_failure_handling(self):
        """Verify retry helper has a max-attempts or failure exit."""
        sh_files = self._find_sh_files()
        for fpath in sh_files:
            content = self._read(fpath)
            if "retry" in content.lower():
                if re.search(
                    r"(max_attempts|MAX_RETRIES|exit\s+1|return\s+1)", content
                ):
                    return
        pytest.fail("Retry helper does not handle max-attempts failure")

    def test_unset_variable_protection(self):
        """Verify 'set -u' or 'nounset' is used for unset variable protection."""
        sh_files = self._find_sh_files()
        assert sh_files, "No shell scripts found"
        for fpath in sh_files:
            content = self._read(fpath)
            if "set -u" in content or "nounset" in content or "set -euo" in content:
                return
        pytest.fail("No script enables unset variable protection (set -u / nounset)")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_sh_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".sh") or f.endswith(".bash"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
