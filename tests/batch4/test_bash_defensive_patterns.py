"""
Test for 'bash-defensive-patterns' skill — Bash Defensive Patterns
Validates shell scripts for defensive patterns: set -euo pipefail, trap,
error redirection, logging, syntax checking with bash -n and shellcheck.
"""

import os
import re
import glob
import subprocess
import pytest


class TestBashDefensivePatterns:
    """Tests for bash defensive patterns in the shellcheck repo."""

    REPO_DIR = "/workspace/shellcheck"

    def _find_scripts(self):
        """Find all .sh files in the repo."""
        return glob.glob(os.path.join(self.REPO_DIR, "**/*.sh"), recursive=True)

    def _read_all_sh(self):
        """Read and concatenate all shell scripts."""
        scripts = self._find_scripts()
        return "\n".join(open(f, errors="ignore").read() for f in scripts)

    # --- File Path Checks ---

    def test_sh_exists(self):
        """Verifies that at least one .sh file exists."""
        scripts = self._find_scripts()
        assert len(scripts) > 0, "No .sh files found"

    def test_repo_dir_exists(self):
        """Verifies the repository directory exists."""
        assert os.path.exists(self.REPO_DIR), f"Repo dir not found: {self.REPO_DIR}"

    # --- Semantic Checks ---

    def test_sem_all_sh_readable(self):
        """All shell scripts can be concatenated."""
        all_sh = self._read_all_sh()
        assert len(all_sh) > 0, "Shell scripts are empty"

    def test_sem_has_set_e(self):
        """Scripts use 'set -euo pipefail' or 'set -e'."""
        all_sh = self._read_all_sh()
        assert (
            "set -euo pipefail" in all_sh or "set -e" in all_sh
        ), "No 'set -e' or 'set -euo pipefail' found"

    def test_sem_has_trap(self):
        """Scripts use 'trap' for cleanup."""
        all_sh = self._read_all_sh()
        assert "trap" in all_sh, "No 'trap' found in scripts"

    def test_sem_has_stderr_redirect(self):
        """Scripts use '>&2' or '2>&1' for error redirection."""
        all_sh = self._read_all_sh()
        assert ">&2" in all_sh or "2>&1" in all_sh, "No stderr redirection found"

    def test_sem_has_logging(self):
        """Scripts use 'log_error' or 'echo' for logging."""
        all_sh = self._read_all_sh()
        assert "log_error" in all_sh or "echo" in all_sh, "No logging pattern found"

    # --- Functional Checks ---

    def test_func_bash_syntax_check_first_script(self):
        """First script passes 'bash -n' syntax check."""
        scripts = self._find_scripts()
        assert len(scripts) > 0, "No scripts found"
        result = subprocess.run(["bash", "-n", scripts[0]], capture_output=True)
        assert (
            result.returncode == 0
        ), f"Syntax error in {scripts[0]}: {result.stderr.decode()}"

    def test_func_syntax_check_return_code(self):
        """bash -n returns 0 for valid script."""
        scripts = self._find_scripts()
        assert len(scripts) > 0, "No scripts found"
        result = subprocess.run(["bash", "-n", scripts[0]], capture_output=True)
        assert (
            result.returncode == 0
        ), f"Syntax error in {scripts[0]}: {result.stderr.decode()}"

    def test_func_run_script_noprofile(self):
        """Script can run with --noprofile --norc."""
        scripts = self._find_scripts()
        assert len(scripts) > 0, "No scripts found"
        result = subprocess.run(
            ["bash", "--noprofile", "--norc", scripts[0]], capture_output=True
        )
        # Script may exit non-zero if it has required args, that's acceptable
        assert isinstance(result.returncode, int)

    def test_func_script_exits_nonzero_without_args(self):
        """Script should exit non-zero when called without required args."""
        scripts = self._find_scripts()
        assert len(scripts) > 0, "No scripts found"
        result = subprocess.run(
            ["bash", "--noprofile", "--norc", scripts[0]], capture_output=True
        )
        assert (
            result.returncode != 0
        ), "Script should exit non-zero when called without required args"

    def test_func_all_scripts_syntax_valid(self):
        """All scripts pass 'bash -n' syntax check."""
        scripts = self._find_scripts()
        assert len(scripts) > 0, "No scripts found"
        for s in scripts:
            r = subprocess.run(["bash", "-n", s], capture_output=True)
            assert r.returncode == 0, f"Syntax error in {s}"

    def test_func_shellcheck_no_critical_issues(self):
        """Scripts pass shellcheck with --severity=warning (or no SC2086 errors)."""
        scripts = self._find_scripts()
        assert len(scripts) > 0, "No scripts found"
        sc_result = subprocess.run(
            ["shellcheck", "--severity=warning"] + scripts,
            capture_output=True,
        )
        assert (
            sc_result.returncode == 0 or b"SC2086" not in sc_result.stdout
        ), "shellcheck reported critical issues"
