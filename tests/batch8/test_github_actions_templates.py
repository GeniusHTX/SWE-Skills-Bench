"""
Test for 'github-actions-templates' skill — GitHub Actions Workflow Templates
Validates that the Agent created CI, release, and deploy workflow YAML files
with triggers, matrix strategy, concurrency, and linting compliance.
"""

import os
import re
import subprocess

import pytest


class TestGithubActionsTemplates:
    """Verify GitHub Actions workflow template implementation."""

    REPO_DIR = "/workspace/starter-workflows"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_ci_yml_exists(self):
        """Verify .github/workflows/ci.yml exists."""
        path = os.path.join(self.REPO_DIR, ".github/workflows/ci.yml")
        assert os.path.isfile(path), ".github/workflows/ci.yml missing"

    def test_release_and_deploy_yml_exist(self):
        """Verify release.yml and deploy.yml exist."""
        for rel in (".github/workflows/release.yml", ".github/workflows/deploy.yml"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_workflows_are_valid_yaml(self):
        """All workflow files are valid YAML."""
        import yaml
        for rel in (".github/workflows/ci.yml",
                     ".github/workflows/release.yml",
                     ".github/workflows/deploy.yml"):
            path = os.path.join(self.REPO_DIR, rel)
            if not os.path.isfile(path):
                pytest.skip(f"{rel} does not exist")
            with open(path, "r") as fh:
                data = yaml.safe_load(fh)
            assert data is not None, f"{rel} parsed to None"

    # ── semantic_check ──────────────────────────────────────────────

    def test_ci_yml_triggers_on_main(self):
        """Verify ci.yml triggers on push and PR to main branch."""
        content = self._read(os.path.join(self.REPO_DIR, ".github/workflows/ci.yml"))
        assert content, "ci.yml is empty or unreadable"
        for kw in ("push", "pull_request", "main"):
            assert kw in content, f"'{kw}' not found in ci.yml"

    def test_test_job_needs_lint(self):
        """Verify test job has needs: [lint] dependency."""
        content = self._read(os.path.join(self.REPO_DIR, ".github/workflows/ci.yml"))
        assert content, "ci.yml is empty or unreadable"
        assert "needs:" in content, "needs: field not found in ci.yml"
        assert "lint" in content, "'lint' not found in ci.yml"

    def test_matrix_strategy_defined(self):
        """Verify test job uses matrix strategy with node and python versions."""
        content = self._read(os.path.join(self.REPO_DIR, ".github/workflows/ci.yml"))
        assert content, "ci.yml is empty or unreadable"
        for kw in ("strategy:", "matrix:", "node-version", "python-version"):
            assert kw in content, f"'{kw}' not found in ci.yml"

    def test_concurrency_cancel_in_progress(self):
        """Verify concurrency group with cancel-in-progress: true is set."""
        content = self._read(os.path.join(self.REPO_DIR, ".github/workflows/ci.yml"))
        assert content, "ci.yml is empty or unreadable"
        assert "concurrency:" in content, "concurrency: block not found"
        assert "cancel-in-progress: true" in content, "cancel-in-progress: true not found"

    # ── functional_check ────────────────────────────────────────────

    def test_yamllint_ci_yml(self):
        """yamllint .github/workflows/ci.yml exits 0."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        path = os.path.join(self.REPO_DIR, ".github/workflows/ci.yml")
        if not os.path.isfile(path):
            pytest.skip("ci.yml does not exist")
        result = subprocess.run(
            ["yamllint", path], capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0 and "command not found" in result.stderr.lower():
            pytest.skip("yamllint not installed")
        assert result.returncode == 0, f"yamllint errors: {result.stderr}"

    def test_actionlint_all_workflows(self):
        """actionlint on all workflow files exits 0."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        result = subprocess.run(
            ["actionlint",
             os.path.join(self.REPO_DIR, ".github/workflows/ci.yml"),
             os.path.join(self.REPO_DIR, ".github/workflows/release.yml"),
             os.path.join(self.REPO_DIR, ".github/workflows/deploy.yml")],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0 and "not found" in (result.stderr + result.stdout).lower():
            pytest.skip("actionlint not installed")
        assert result.returncode == 0, f"actionlint errors: {result.stderr}"

    def test_release_triggers_on_version_tags(self):
        """Verify release.yml triggers only on tags matching v* pattern."""
        content = self._read(os.path.join(self.REPO_DIR, ".github/workflows/release.yml"))
        assert content, "release.yml is empty or unreadable"
        found = any(kw in content for kw in ("tags:", "v*", r"v\.*\.*\.*"))
        assert found, "No tag pattern found in release.yml trigger"
