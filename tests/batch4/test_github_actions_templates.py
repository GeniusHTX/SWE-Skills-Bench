"""
Test for 'github-actions-templates' skill — CI/CD Workflow Templates
Validates that the Agent created proper GitHub Actions CI and CD workflow
YAML files with lint, test, matrix, coverage, Docker, and secret management.
"""

import os
import re

import pytest
import yaml


class TestGithubActionsTemplates:
    """Verify GitHub Actions CI/CD workflow templates."""

    REPO_DIR = "/workspace/starter-workflows"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _ci_path(self):
        return os.path.join(self.REPO_DIR, ".github/workflows/ci.yml")

    def _cd_path(self):
        return os.path.join(self.REPO_DIR, ".github/workflows/cd.yml")

    def _load_ci(self):
        return yaml.safe_load(open(self._ci_path()).read())

    def _load_cd(self):
        return yaml.safe_load(open(self._cd_path()).read())

    # ---- file_path_check ----

    def test_ci_yml_exists(self):
        """Verifies .github/workflows/ci.yml exists."""
        assert os.path.exists(self._ci_path()), "ci.yml not found"

    def test_cd_yml_exists(self):
        """Verifies .github/workflows/cd.yml exists."""
        assert os.path.exists(self._cd_path()), "cd.yml not found"

    # ---- semantic_check ----

    def test_sem_ci_valid_yaml(self):
        """Verifies ci.yml is valid YAML with 'on' and 'jobs'."""
        ci = self._load_ci()
        assert "on" in ci or True in ci, "'on' key missing in ci.yml"
        assert "jobs" in ci, "'jobs' key missing in ci.yml"

    def test_sem_cd_valid_yaml(self):
        """Verifies cd.yml is valid YAML with 'on' and 'jobs'."""
        cd = self._load_cd()
        assert "on" in cd or True in cd, "'on' key missing in cd.yml"
        assert "jobs" in cd, "'jobs' key missing in cd.yml"

    def test_sem_ci_push_trigger(self):
        """Verifies ci.yml has push trigger."""
        ci = self._load_ci()
        on_cfg = ci.get("on") or ci.get(True, {})
        if isinstance(on_cfg, dict):
            assert "push" in on_cfg, "ci.yml missing 'push' trigger"
        # If 'on' is a list, check if 'push' is in it
        elif isinstance(on_cfg, list):
            assert "push" in on_cfg, "ci.yml missing 'push' trigger"

    def test_sem_ci_pull_request_trigger(self):
        """Verifies ci.yml has pull_request trigger (edge case)."""
        ci = self._load_ci()
        on_cfg = ci.get("on") or ci.get(True, {})
        if isinstance(on_cfg, dict):
            assert "pull_request" in on_cfg, "ci.yml missing 'pull_request' trigger"
        elif isinstance(on_cfg, list):
            assert "pull_request" in on_cfg, "ci.yml missing 'pull_request' trigger"

    def test_sem_ci_matrix_strategy(self):
        """Verifies at least one job uses matrix strategy."""
        ci = self._load_ci()
        assert any(
            "matrix" in str(job.get("strategy", {})) for job in ci["jobs"].values()
        ), "No matrix strategy found in ci.yml jobs"

    def test_sem_cd_tag_trigger(self):
        """Verifies cd.yml triggers on tag push."""
        cd = self._load_cd()
        on_cfg = cd.get("on") or cd.get(True, {})
        if isinstance(on_cfg, dict):
            assert (
                on_cfg.get("push", {}).get("tags") is not None
            ), "cd.yml missing tag trigger"

    # ---- functional_check ----

    def test_func_ci_has_lint_job(self):
        """Verifies CI has a lint job with flake8 or ruff."""
        ci = self._load_ci()
        ci_jobs = ci["jobs"]
        assert any(
            "lint" in name or "flake8" in str(job) or "ruff" in str(job)
            for name, job in ci_jobs.items()
        ), "No lint job found in ci.yml"

    def test_func_ci_has_pytest(self):
        """Verifies CI has a pytest step."""
        ci = self._load_ci()
        ci_jobs = ci["jobs"]
        assert any(
            "pytest" in str(job) for job in ci_jobs.values()
        ), "No pytest step found in ci.yml"

    def test_func_ci_python_version_matrix(self):
        """Verifies CI matrix has >= 2 Python versions."""
        ci = self._load_ci()
        ci_jobs = ci["jobs"]
        python_versions = [
            str(v)
            for job in ci_jobs.values()
            for v in job.get("strategy", {}).get("matrix", {}).get("python-version", [])
        ]
        assert (
            len(python_versions) >= 2
        ), f"Expected >= 2 Python versions, got {len(python_versions)}"

    def test_func_ci_coverage(self):
        """Verifies CI has coverage reporting."""
        ci = self._load_ci()
        ci_jobs = ci["jobs"]
        assert any(
            "cov-fail-under" in str(job) or "coverage" in str(job).lower()
            for job in ci_jobs.values()
        ), "No coverage configuration found in ci.yml"

    def test_func_cd_has_docker_or_build(self):
        """Verifies CD has a Docker or build job."""
        cd = self._load_cd()
        cd_jobs = cd["jobs"]
        assert any(
            "docker" in str(job).lower() or "build" in name.lower()
            for name, job in cd_jobs.items()
        ), "No Docker/build job in cd.yml"

    def test_func_cd_has_needs(self):
        """Verifies CD jobs use 'needs' for dependencies."""
        cd = self._load_cd()
        cd_jobs = cd["jobs"]
        assert any(
            "needs" in str(job) for job in cd_jobs.values()
        ), "No 'needs' dependency in cd.yml"

    def test_func_secrets_reference(self):
        """Verifies workflows reference secrets."""
        workflow_text = self._read(self._ci_path()) + self._read(self._cd_path())
        assert (
            "${{ secrets." in workflow_text
        ), "No ${{ secrets. }} reference in workflows"

    def test_func_no_hardcoded_passwords(self):
        """Verifies no hardcoded passwords in workflows."""
        workflow_text = self._read(self._ci_path()) + self._read(self._cd_path())
        assert not re.search(
            r"password\s*=\s*[\"'][^$\{]", workflow_text, re.IGNORECASE
        ), "Hardcoded password found in workflow"

    def test_func_failure_hardcoded_password(self):
        """Failure case: no hardcoded passwords should exist."""
        workflow_text = self._read(self._ci_path()) + self._read(self._cd_path())
        matches = re.findall(
            r"password\s*=\s*[\"'][^$\{]", workflow_text, re.IGNORECASE
        )
        assert len(matches) == 0, f"Hardcoded passwords found: {matches}"
