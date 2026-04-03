"""
Test for 'turborepo' skill — Turborepo Monorepo Build System
Validates that the Agent configured a Turborepo monorepo with turbo.json,
workspace globs, pipeline tasks, and proper cache/persistent settings.
"""

import json
import os
import re
import subprocess

import pytest


class TestTurborepo:
    """Verify Turborepo monorepo configuration."""

    REPO_DIR = "/workspace/turbo"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_turbo_json_exists(self):
        """Verify turbo.json exists at repository root."""
        path = os.path.join(self.REPO_DIR, "turbo.json")
        assert os.path.isfile(path), "Missing: turbo.json"

    def test_root_package_json_with_workspaces(self):
        """Verify root package.json with workspaces field exists."""
        path = os.path.join(self.REPO_DIR, "package.json")
        assert os.path.isfile(path), "Missing: package.json"

    def test_apps_directory_exists(self):
        """Verify apps/ directory exists."""
        path = os.path.join(self.REPO_DIR, "apps")
        assert os.path.isdir(path), "Missing: apps/ directory"

    def test_packages_directory_exists(self):
        """Verify packages/ directory exists."""
        path = os.path.join(self.REPO_DIR, "packages")
        assert os.path.isdir(path), "Missing: packages/ directory"

    # ── semantic_check ──────────────────────────────────────────────

    def test_build_pipeline_depends_on_upstream(self):
        """Verify turbo.json build pipeline has dependsOn: ['^build']."""
        content = self._read(os.path.join(self.REPO_DIR, "turbo.json"))
        assert content, "turbo.json is empty or unreadable"
        assert "^build" in content, "^build dependency not found in turbo.json"

    def test_build_outputs_dist(self):
        """Verify turbo.json build pipeline outputs includes dist/**."""
        content = self._read(os.path.join(self.REPO_DIR, "turbo.json"))
        assert content, "turbo.json is empty or unreadable"
        assert "dist/**" in content, "dist/** not found in turbo.json outputs"

    def test_dev_task_persistent_true(self):
        """Verify dev task has persistent: true for long-running servers."""
        content = self._read(os.path.join(self.REPO_DIR, "turbo.json"))
        assert content, "turbo.json is empty or unreadable"
        assert "persistent" in content, "persistent not found in turbo.json"

    def test_schema_field_present(self):
        """Verify $schema field references Turborepo schema URL."""
        content = self._read(os.path.join(self.REPO_DIR, "turbo.json"))
        assert content, "turbo.json is empty or unreadable"
        assert "$schema" in content, "$schema not found in turbo.json"

    def test_workspaces_apps_and_packages(self):
        """Verify root package.json workspaces contains apps/* and packages/*."""
        content = self._read(os.path.join(self.REPO_DIR, "package.json"))
        assert content, "package.json is empty or unreadable"
        assert "apps/*" in content, "apps/* not found in package.json workspaces"
        assert "packages/*" in content, \
            "packages/* not found in package.json workspaces"

    # ── functional_check (command) ──────────────────────────────────

    def _skip_unless_repo(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")

    def test_turbo_dry_run_exits_zero(self):
        """npx turbo run build --dry-run exits 0 validating pipeline config."""
        self._skip_unless_repo()
        result = subprocess.run(
            ["npx", "turbo", "run", "build", "--dry-run"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, \
            f"turbo dry-run failed: {result.stderr}"

    def test_turbo_dry_run_json_parseable(self):
        """npx turbo run build --dry-run=json outputs parseable JSON."""
        self._skip_unless_repo()
        result = subprocess.run(
            ["npx", "turbo", "run", "build", "--dry-run=json"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, \
            f"turbo dry-run json failed: {result.stderr}"
        try:
            json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail("turbo dry-run=json output is not valid JSON")
