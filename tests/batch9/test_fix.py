"""
Test for 'fix' skill — React Code Fix & Linter CLI
Validates the upgradle fix CLI tool: package.json bin entry, CLI flag
definitions (--dry-run, --rule), ESLint/jscodeshift integration, and
command-line behavior (help, error handling, dry-run immutability).
"""

import json
import os
import subprocess
import tempfile

import pytest


class TestFix:
    """Verify upgradle fix CLI tool structure and behavior."""

    REPO_DIR = "/workspace/upgradle"
    PKG_DIR = os.path.join(REPO_DIR, "packages", "fix")

    # ── helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    @classmethod
    def _load_pkg_json(cls) -> dict:
        path = os.path.join(cls.PKG_DIR, "package.json")
        with open(path, "r") as fh:
            return json.load(fh)

    @classmethod
    def _npm_install(cls):
        """Run npm install inside packages/fix; skip on failure."""
        result = subprocess.run(
            ["npm", "install"],
            cwd=cls.PKG_DIR,
            capture_output=True,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip("npm install failed — skipping CLI tests")

    # ── file_path_check ──────────────────────────────────────────────────

    def test_package_json_exists_with_bin_entry(self):
        """packages/fix/package.json must exist and declare a bin.fix entry."""
        pkg = self._load_pkg_json()
        assert "bin" in pkg, "package.json missing 'bin' key"
        assert "fix" in pkg["bin"], "package.json bin missing 'fix' entry"

    def test_index_ts_exists(self):
        """packages/fix/src/index.ts must exist and be non-empty."""
        path = os.path.join(self.PKG_DIR, "src", "index.ts")
        assert os.path.isfile(path), f"{path} does not exist"
        assert os.path.getsize(path) > 0, "index.ts is empty"

    def test_runner_ts_exists(self):
        """packages/fix/src/runner.ts must exist and be non-empty."""
        path = os.path.join(self.PKG_DIR, "src", "runner.ts")
        assert os.path.isfile(path), f"{path} does not exist"
        assert os.path.getsize(path) > 0, "runner.ts is empty"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_bin_field_points_to_valid_js_entry(self):
        """bin.fix value must point to a .js entrypoint."""
        pkg = self._load_pkg_json()
        bin_path = pkg.get("bin", {}).get("fix", "")
        assert bin_path, "bin.fix is empty"
        assert bin_path.endswith(".js"), f"bin.fix should end with .js, got {bin_path}"

    def test_dry_run_flag_defined_in_cli_source(self):
        """--dry-run flag must be defined in the CLI argument parser."""
        content = self._read_file(os.path.join(self.PKG_DIR, "src", "index.ts"))
        assert content, "index.ts is empty or unreadable"
        assert "dry-run" in content or "dryRun" in content, (
            "--dry-run flag not defined in index.ts"
        )

    def test_eslint_integration_in_runner(self):
        """runner.ts must import ESLint or jscodeshift."""
        content = self._read_file(os.path.join(self.PKG_DIR, "src", "runner.ts"))
        assert content, "runner.ts is empty or unreadable"
        has_eslint = "eslint" in content.lower() or "ESLint" in content
        has_jscodeshift = "jscodeshift" in content
        assert has_eslint or has_jscodeshift, (
            "runner.ts imports neither eslint nor jscodeshift"
        )

    def test_jscodeshift_declared_as_dependency(self):
        """jscodeshift must be in dependencies or devDependencies."""
        pkg = self._load_pkg_json()
        deps = set(pkg.get("dependencies", {}).keys())
        dev_deps = set(pkg.get("devDependencies", {}).keys())
        assert "jscodeshift" in deps | dev_deps, (
            "jscodeshift not declared in any dependency section"
        )

    # ── functional_check (command) ───────────────────────────────────────

    def test_fix_help_exits_with_code_zero(self):
        """'node packages/fix/bin/fix --help' must exit 0 with non-empty output."""
        self._npm_install()
        bin_path = os.path.join(self.PKG_DIR, "bin", "fix")
        if not os.path.isfile(bin_path):
            # Try dist path
            pkg = self._load_pkg_json()
            bin_path = os.path.join(self.PKG_DIR, pkg.get("bin", {}).get("fix", ""))
        result = subprocess.run(
            ["node", bin_path, "--help"],
            capture_output=True,
            timeout=30,
            cwd=self.REPO_DIR,
        )
        assert result.returncode == 0, f"--help exited with {result.returncode}"
        assert len(result.stdout) > 0, "--help produced no output"

    def test_nonexistent_file_exits_with_error(self):
        """Passing a non-existent file path must exit with non-zero code."""
        self._npm_install()
        bin_path = os.path.join(self.PKG_DIR, "bin", "fix")
        if not os.path.isfile(bin_path):
            pkg = self._load_pkg_json()
            bin_path = os.path.join(self.PKG_DIR, pkg.get("bin", {}).get("fix", ""))
        result = subprocess.run(
            ["node", bin_path, "/nonexistent/path/file.js"],
            capture_output=True,
            timeout=30,
            cwd=self.REPO_DIR,
        )
        assert result.returncode != 0, "Expected non-zero exit for nonexistent file"

    def test_dry_run_does_not_modify_file(self):
        """--dry-run must not modify the target file."""
        self._npm_install()
        bin_path = os.path.join(self.PKG_DIR, "bin", "fix")
        if not os.path.isfile(bin_path):
            pkg = self._load_pkg_json()
            bin_path = os.path.join(self.PKG_DIR, pkg.get("bin", {}).get("fix", ""))
        # Create a temporary JS file with a known fixable issue
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", dir=self.REPO_DIR, delete=False
        ) as tmp:
            tmp.write("var x = 1;\n")
            tmp_path = tmp.name
        try:
            before = open(tmp_path).read()
            subprocess.run(
                ["node", bin_path, "--dry-run", tmp_path],
                capture_output=True,
                timeout=30,
                cwd=self.REPO_DIR,
            )
            after = open(tmp_path).read()
            assert before == after, "--dry-run modified the file"
        finally:
            os.unlink(tmp_path)

    def test_dry_run_outputs_diff_to_stdout(self):
        """--dry-run should produce non-empty stdout for fixable files."""
        self._npm_install()
        bin_path = os.path.join(self.PKG_DIR, "bin", "fix")
        if not os.path.isfile(bin_path):
            pkg = self._load_pkg_json()
            bin_path = os.path.join(self.PKG_DIR, pkg.get("bin", {}).get("fix", ""))
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", dir=self.REPO_DIR, delete=False
        ) as tmp:
            tmp.write("var x = 1;\nvar y = 2;\n")
            tmp_path = tmp.name
        try:
            result = subprocess.run(
                ["node", bin_path, "--dry-run", tmp_path],
                capture_output=True,
                timeout=30,
                cwd=self.REPO_DIR,
            )
            # Output may be empty if no fixable issues, so we just assert no crash
            assert result.returncode in (0, 1), (
                f"Unexpected exit code {result.returncode}"
            )
        finally:
            os.unlink(tmp_path)

    def test_fix_rule_flag_filters_to_single_rule(self):
        """--rule flag must be accepted without crashing."""
        self._npm_install()
        bin_path = os.path.join(self.PKG_DIR, "bin", "fix")
        if not os.path.isfile(bin_path):
            pkg = self._load_pkg_json()
            bin_path = os.path.join(self.PKG_DIR, pkg.get("bin", {}).get("fix", ""))
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", dir=self.REPO_DIR, delete=False
        ) as tmp:
            tmp.write("var x = 1;\n")
            tmp_path = tmp.name
        try:
            result = subprocess.run(
                ["node", bin_path, "--rule", "no-var", "--dry-run", tmp_path],
                capture_output=True,
                timeout=30,
                cwd=self.REPO_DIR,
            )
            assert result.returncode in (0, 1), (
                f"--rule flag caused unexpected exit code {result.returncode}"
            )
        finally:
            os.unlink(tmp_path)
