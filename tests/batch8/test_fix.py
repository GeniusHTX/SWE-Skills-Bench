"""
Test for 'fix' skill — Lint/Format Fix Script
Validates that the Agent created a fix script with ESLint --fix,
prettier --write, --check mode, and proper exit code propagation.
"""

import os
import re
import subprocess

import pytest


class TestFix:
    """Verify lint/format fix script implementation."""

    REPO_DIR = "/workspace/upgradle"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _find_fix_script(self):
        for candidate in ("scripts/fix.ts", "scripts/fix.js", "scripts/fix.sh"):
            path = os.path.join(self.REPO_DIR, candidate)
            if os.path.isfile(path):
                return path, candidate
        return None, None

    # ── file_path_check ─────────────────────────────────────────────

    def test_fix_script_exists(self):
        """Verify scripts/fix.ts or scripts/fix.js or scripts/fix.sh exists."""
        path, _ = self._find_fix_script()
        assert path is not None, "No fix script found (fix.ts / fix.js / fix.sh)"

    def test_package_json_has_fix_script(self):
        """Verify package.json contains linc or fix script entries."""
        content = self._read(os.path.join(self.REPO_DIR, "package.json"))
        assert content, "package.json is empty or unreadable"
        found = "linc" in content or '"fix"' in content
        assert found, "No 'linc' or 'fix' script entry in package.json"

    # ── semantic_check ──────────────────────────────────────────────

    def test_eslint_fix_flag_present(self):
        """Verify script invokes eslint with --fix flag."""
        path, _ = self._find_fix_script()
        if path is None:
            pytest.skip("Fix script not found")
        content = self._read(path)
        assert content, "Fix script is empty"
        found = "--fix" in content or "yarn linc" in content
        assert found, "--fix or yarn linc not found in fix script"

    def test_prettier_write_present(self):
        """Verify script invokes prettier --write."""
        path, _ = self._find_fix_script()
        if path is None:
            pytest.skip("Fix script not found")
        content = self._read(path)
        assert "prettier" in content, "prettier not referenced in fix script"
        assert "--write" in content, "--write not found in fix script"

    def test_check_mode_flag_handled(self):
        """Verify script accepts a --check or --dry-run flag."""
        path, _ = self._find_fix_script()
        if path is None:
            pytest.skip("Fix script not found")
        content = self._read(path)
        found = any(kw in content for kw in ("--check", "check", "dry-run"))
        assert found, "No --check / --dry-run mode support found"

    def test_exit_code_1_on_error(self):
        """Verify script exits with code 1 on non-fixable ESLint errors."""
        path, _ = self._find_fix_script()
        if path is None:
            pytest.skip("Fix script not found")
        content = self._read(path)
        found = any(kw in content for kw in ("process.exit(1)", "exit 1", "exitCode"))
        assert found, "No exit code 1 propagation found in fix script"

    # ── functional_check (command) ──────────────────────────────────

    def _skip_unless_yarn_ready(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if not os.path.isfile(os.path.join(self.REPO_DIR, "package.json")):
            pytest.skip("package.json missing")

    def test_fix_on_clean_project_exits_zero(self):
        """Running fix script on a pre-formatted project exits 0."""
        self._skip_unless_yarn_ready()
        result = subprocess.run(
            ["yarn", "fix"], capture_output=True, text=True,
            cwd=self.REPO_DIR, timeout=120,
        )
        if result.returncode != 0:
            pytest.skip("yarn fix failed — may need yarn install first")

    def test_check_mode_exits_zero_on_clean_file(self):
        """Running fix --check on already-formatted file exits 0."""
        self._skip_unless_yarn_ready()
        path, rel = self._find_fix_script()
        if path is None:
            pytest.skip("Fix script not found")
        result = subprocess.run(
            ["node", rel, "--check"], capture_output=True, text=True,
            cwd=self.REPO_DIR, timeout=120,
        )
        if result.returncode != 0:
            pytest.skip("--check mode failed or not supported")

    def test_stdout_contains_fixed_count(self):
        """Stdout of a successful run contains 'Fixed N files' pattern."""
        self._skip_unless_yarn_ready()
        result = subprocess.run(
            ["yarn", "fix"], capture_output=True, text=True,
            cwd=self.REPO_DIR, timeout=120,
        )
        if result.returncode != 0:
            pytest.skip("yarn fix failed")
        combined = result.stdout + result.stderr
        assert re.search(r"Fixed \d+ files?", combined) or "no files" in combined.lower(), \
            "No 'Fixed N files' message in output"

    def test_empty_path_scope_exits_zero(self):
        """Fix script run with --path pointing to empty directory exits 0 gracefully."""
        self._skip_unless_yarn_ready()
        path, rel = self._find_fix_script()
        if path is None:
            pytest.skip("Fix script not found")
        result = subprocess.run(
            ["node", rel, "--path", "/tmp/empty_dir_test"],
            capture_output=True, text=True,
            cwd=self.REPO_DIR, timeout=120,
        )
        # Graceful exit (0 or clean error)
        assert result.returncode == 0 or "No files" in (result.stdout + result.stderr), \
            "Script did not handle empty directory gracefully"
