"""
Test for 'bash-defensive-patterns' skill — Bash Defensive Scripting
Validates set -euo pipefail, trap cleanup, mktemp usage, command -v,
shebang, and script syntax via static analysis and subprocess checks.
"""

import glob
import os
import subprocess

import pytest


class TestBashDefensivePatterns:
    """Verify bash defensive patterns: error handling, cleanup, security."""

    REPO_DIR = "/workspace/shellcheck"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _bash(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "examples", "bash", *parts)

    def _all_scripts(self) -> list:
        return glob.glob(self._bash("*.sh"))

    # ── file_path_check ──────────────────────────────────────────────────

    def test_bash_scripts_exist(self):
        """examples/bash/ must contain at least one .sh script."""
        scripts = self._all_scripts()
        assert len(scripts) >= 1, "No .sh scripts in examples/bash/"

    def test_utility_library_exists(self):
        """scripts/lib/ or scripts/common.sh must exist."""
        lib = os.path.join(self.REPO_DIR, "scripts", "lib")
        common = os.path.join(self.REPO_DIR, "scripts", "common.sh")
        has_lib = os.path.isdir(lib) and len(glob.glob(os.path.join(lib, "*.sh"))) > 0
        assert has_lib or os.path.isfile(common), "No utility library found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_set_euo_pipefail(self):
        """Every .sh script must contain 'set -euo pipefail'."""
        for script in self._all_scripts():
            content = self._read_file(script)
            assert "set -euo pipefail" in content, f"Missing set -euo pipefail in {script}"

    def test_trap_cleanup_on_exit(self):
        """Scripts must have trap ... EXIT for cleanup."""
        scripts = self._all_scripts()
        if not scripts:
            pytest.skip("No scripts found")
        for script in scripts:
            content = self._read_file(script)
            has_trap = "trap" in content and "EXIT" in content
            assert has_trap, f"No trap EXIT in {script}"

    def test_mktemp_not_hardcoded_tmp(self):
        """Temp files must use mktemp, not hardcoded /tmp/ paths."""
        for script in self._all_scripts():
            content = self._read_file(script)
            if "/tmp/" in content:
                # Check for hardcoded fixed filenames
                import re
                hardcoded = re.findall(r"/tmp/[a-zA-Z][\w.-]+", content)
                if hardcoded:
                    assert "mktemp" in content, f"Hardcoded /tmp/ path without mktemp in {script}"

    def test_command_v_not_which(self):
        """Dependency checks must use 'command -v', not 'which'."""
        for script in self._all_scripts():
            content = self._read_file(script)
            if "command -v" in content:
                continue
            # If which is used for dependency checking, flag it
            lines = content.split("\n")
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "which " in stripped:
                    pytest.fail(f"'which' used instead of 'command -v' in {script}")

    # ── functional_check ─────────────────────────────────────────────────

    def test_bash_syntax_check(self):
        """All .sh scripts must pass bash -n syntax validation."""
        try:
            subprocess.run(["bash", "--version"], capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("bash not available")
        for script in self._all_scripts():
            r = subprocess.run(["bash", "-n", script], capture_output=True, text=True, timeout=30)
            assert r.returncode == 0, f"Syntax error in {script}: {r.stderr}"

    def test_shellcheck_passes(self):
        """Scripts must pass shellcheck without errors."""
        try:
            subprocess.run(["shellcheck", "--version"], capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("shellcheck not available")
        for script in self._all_scripts():
            r = subprocess.run(["shellcheck", script], capture_output=True, text=True, timeout=30)
            assert r.returncode == 0, f"shellcheck errors in {script}: {r.stdout}"

    def test_missing_args_exits_with_1(self):
        """Script without required args must exit with code 1."""
        scripts = self._all_scripts()
        if not scripts:
            pytest.skip("No scripts found")
        script = scripts[0]
        try:
            r = subprocess.run(
                ["bash", script], capture_output=True, text=True, timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("bash not available")
        # Script should exit non-zero without arguments
        assert r.returncode != 0, "Script should fail without arguments"

    def test_shebang_is_bash(self):
        """Each script must use #!/usr/bin/env bash or #!/bin/bash, not #!/bin/sh."""
        for script in self._all_scripts():
            content = self._read_file(script)
            first_line = content.split("\n")[0] if content else ""
            assert first_line.startswith("#!"), f"No shebang in {script}"
            assert "bash" in first_line, f"Shebang is not bash in {script}: {first_line}"

    def test_empty_string_arg_treated_as_missing(self):
        """Empty string argument must be treated as missing."""
        scripts = self._all_scripts()
        if not scripts:
            pytest.skip("No scripts found")
        script = scripts[0]
        try:
            r = subprocess.run(
                ["bash", script, ""], capture_output=True, text=True, timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("bash not available")
        assert r.returncode != 0, "Script should reject empty string argument"
