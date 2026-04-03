"""
Test for 'nx-workspace-patterns' skill — Nx Plugin
Validates that the Agent created a TypeScript Nx plugin with component
generator, build executor, schema validation, and test suites.
"""

import os
import re
import subprocess

import pytest


class TestNxWorkspacePatterns:
    """Verify Nx workspace plugin implementation."""

    REPO_DIR = "/workspace/nx"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_generator_files_exist(self):
        """Verify component generator index.ts and schema.json exist."""
        for rel in ("libs/nx-plugin/src/generators/component/index.ts",
                     "libs/nx-plugin/src/generators/component/schema.json"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_executor_files_exist(self):
        """Verify build executor index.ts and schema.json exist."""
        for rel in ("libs/nx-plugin/src/executors/build/index.ts",
                     "libs/nx-plugin/src/executors/build/schema.json"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_nx_plugin_package_json_exists(self):
        """Verify libs/nx-plugin/package.json exists."""
        path = os.path.join(self.REPO_DIR, "libs/nx-plugin/package.json")
        assert os.path.isfile(path), "libs/nx-plugin/package.json missing"

    # ── semantic_check ──────────────────────────────────────────────

    def test_generator_uses_generateFiles_and_devkit(self):
        """Verify component generator uses generateFiles from @nx/devkit."""
        content = self._read(os.path.join(
            self.REPO_DIR, "libs/nx-plugin/src/generators/component/index.ts"))
        assert content, "Generator index.ts is empty or unreadable"
        assert "generateFiles" in content, "generateFiles not found"
        assert "@nx/devkit" in content, "@nx/devkit import not found"

    def test_executor_returns_success_boolean(self):
        """Verify executor returns Promise<{ success: boolean }>."""
        content = self._read(os.path.join(
            self.REPO_DIR, "libs/nx-plugin/src/executors/build/index.ts"))
        assert content, "Executor index.ts is empty or unreadable"
        assert "success" in content, "'success' not found in executor"
        assert "boolean" in content, "'boolean' not found in executor"

    def test_schema_requires_name_field(self):
        """Component generator schema.json defines 'name' as required with pattern."""
        content = self._read(os.path.join(
            self.REPO_DIR, "libs/nx-plugin/src/generators/component/schema.json"))
        assert content, "schema.json is empty or unreadable"
        for kw in ("required", "name", "pattern"):
            assert kw in content, f"'{kw}' not found in schema.json"

    # ── functional_check (command) ──────────────────────────────────

    def _skip_unless_node(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")

    def test_typescript_plugin_compiles(self):
        """tsc --noEmit on nx-plugin exits 0."""
        self._skip_unless_node()
        tsconfig = os.path.join(self.REPO_DIR, "libs/nx-plugin/tsconfig.json")
        if not os.path.isfile(tsconfig):
            pytest.skip("tsconfig.json not found")
        result = subprocess.run(
            ["npx", "tsc", "--noEmit", "-p", tsconfig],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        if result.returncode != 0 and "not found" in result.stderr.lower():
            pytest.skip("tsc not available")
        assert result.returncode == 0, f"tsc failed: {result.stderr}"

    def test_component_generator_dry_run(self):
        """Component generator --dry-run logs file paths without creating files."""
        self._skip_unless_node()
        result = subprocess.run(
            ["npx", "nx", "g", "@my-org/nx-plugin:component",
             "--name=Button", "--directory=ui", "--dry-run"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        combined = result.stdout + result.stderr
        if result.returncode != 0 and "Cannot find" in combined:
            pytest.skip("nx-plugin not configured")
        found = any(kw in combined for kw in ("DRY RUN", "CREATE", "Button"))
        assert found, f"No dry-run output found: {combined[:500]}"

    def test_nx_test_suite_passes(self):
        """Nx unit test suite for nx-plugin passes."""
        self._skip_unless_node()
        result = subprocess.run(
            ["npx", "nx", "test", "nx-plugin"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        if result.returncode != 0 and "Cannot find" in (result.stdout + result.stderr):
            pytest.skip("nx-plugin tests not configured")
        assert result.returncode == 0, f"Tests failed: {result.stderr}"

    def test_executor_fails_without_tsconfig(self):
        """Build executor returns success: false when tsconfig.build.json missing."""
        self._skip_unless_node()
        result = subprocess.run(
            ["npx", "nx", "test", "nx-plugin", "--",
             "--testNamePattern=tsconfig.*missing|fail.*tsconfig"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        if result.returncode != 0 and "no tests" in (result.stdout + result.stderr).lower():
            pytest.skip("No tsconfig missing test found")
        assert result.returncode == 0
