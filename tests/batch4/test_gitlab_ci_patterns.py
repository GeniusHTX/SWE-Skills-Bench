"""
Test for 'gitlab-ci-patterns' skill — GitLab CI Patterns
Validates .gitlab-ci.yml for stages, jobs, test/build/deploy ordering,
artifacts, coverage, and production deployment guards.
"""

import os
import re
import yaml
import pytest


class TestGitlabCiPatterns:
    """Tests for GitLab CI patterns in the gitlabhq repo."""

    REPO_DIR = "/workspace/gitlabhq"

    def _read(self, relpath):
        full = os.path.join(self.REPO_DIR, relpath)
        with open(full, "r", errors="ignore") as f:
            return f.read()

    def _load_ci(self):
        """Load and parse .gitlab-ci.yml."""
        content = self._read(".gitlab-ci.yml")
        return yaml.safe_load(content)

    def _get_ci_jobs(self, ci):
        """Extract jobs (dict entries with 'script' key) from CI config."""
        return {k: v for k, v in ci.items() if isinstance(v, dict) and "script" in v}

    # --- File Path Checks ---

    def test_gitlab_ci_yml_exists(self):
        """Verifies that .gitlab-ci.yml exists."""
        path = os.path.join(self.REPO_DIR, ".gitlab-ci.yml")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_repo_dir_exists(self):
        """Verifies the repository directory exists."""
        assert os.path.exists(self.REPO_DIR), f"Repo dir not found: {self.REPO_DIR}"

    # --- Semantic Checks ---

    def test_sem_ci_parseable(self):
        """CI config is valid YAML."""
        ci = self._load_ci()
        assert isinstance(ci, dict), "CI config is not a valid YAML dict"

    def test_sem_has_stages(self):
        """CI config has 'stages' key."""
        ci = self._load_ci()
        assert "stages" in ci, "'stages' not found in CI config"

    def test_sem_required_stages(self):
        """CI config has test, build, deploy stages."""
        ci = self._load_ci()
        required_stages = {"test", "build", "deploy"}
        assert required_stages.issubset(
            set(ci["stages"])
        ), f"Missing stages: {required_stages - set(ci['stages'])}"

    def test_sem_has_jobs_with_script(self):
        """CI config has jobs with 'script' key."""
        ci = self._load_ci()
        ci_jobs = self._get_ci_jobs(ci)
        assert len(ci_jobs) > 0, "No jobs with 'script' found"

    # --- Functional Checks ---

    def test_func_test_before_build(self):
        """'test' stage comes before 'build' stage."""
        ci = self._load_ci()
        stages = ci["stages"]
        assert stages.index("test") < stages.index(
            "build"
        ), "test stage must come before build"

    def test_func_build_before_deploy(self):
        """'build' stage comes before 'deploy' stage."""
        ci = self._load_ci()
        stages = ci["stages"]
        assert stages.index("build") < stages.index(
            "deploy"
        ), "build stage must come before deploy"

    def test_func_has_test_jobs(self):
        """At least one job with stage='test' exists."""
        ci = self._load_ci()
        ci_jobs = self._get_ci_jobs(ci)
        test_jobs = [j for j in ci_jobs.values() if j.get("stage") == "test"]
        assert len(test_jobs) >= 1, "No test jobs found"

    def test_func_test_job_runs_tests(self):
        """Test jobs run pytest or test commands."""
        ci = self._load_ci()
        ci_jobs = self._get_ci_jobs(ci)
        test_jobs = [j for j in ci_jobs.values() if j.get("stage") == "test"]
        assert any(
            "pytest" in str(j.get("script", []))
            or "test" in str(j.get("script", [])).lower()
            for j in test_jobs
        ), "No test job runs pytest or test"

    def test_func_test_job_has_junit_report(self):
        """Test jobs produce JUnit artifacts."""
        ci = self._load_ci()
        ci_jobs = self._get_ci_jobs(ci)
        test_jobs = [j for j in ci_jobs.values() if j.get("stage") == "test"]
        assert any(
            j.get("artifacts", {}).get("reports", {}).get("junit") for j in test_jobs
        ), "No test job has JUnit report artifacts"

    def test_func_test_job_has_coverage(self):
        """Test jobs produce coverage reports."""
        ci = self._load_ci()
        ci_jobs = self._get_ci_jobs(ci)
        test_jobs = [j for j in ci_jobs.values() if j.get("stage") == "test"]
        assert any(
            j.get("artifacts", {}).get("reports", {}).get("coverage_report")
            or "coverage" in str(j.get("artifacts", {}))
            for j in test_jobs
        ), "No test job has coverage report artifacts"

    def test_func_has_deploy_jobs(self):
        """At least one job with stage='deploy' exists."""
        ci = self._load_ci()
        ci_jobs = self._get_ci_jobs(ci)
        deploy_jobs = [j for j in ci_jobs.values() if j.get("stage") == "deploy"]
        assert len(deploy_jobs) >= 1, "No deploy jobs found"

    def test_func_prod_deploy_is_manual(self):
        """Production deploy jobs require manual trigger."""
        ci = self._load_ci()
        ci_jobs = self._get_ci_jobs(ci)
        deploy_jobs = [j for j in ci_jobs.values() if j.get("stage") == "deploy"]
        prod_jobs = [
            j
            for j in deploy_jobs
            if "prod" in str(j.get("environment", {}).get("name", "")).lower()
            or "production" in str(j)
        ]
        if prod_jobs:
            assert any(
                j.get("when") == "manual" for j in prod_jobs
            ), "Production deploy is not set to manual"

    def test_func_failure_missing_deploy_stage(self):
        """Failure case: validates deploy stage exists."""
        ci = self._load_ci()
        assert "deploy" in ci.get("stages", []), "Missing 'deploy' stage"
