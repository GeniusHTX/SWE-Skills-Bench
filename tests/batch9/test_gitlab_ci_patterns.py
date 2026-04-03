"""
Test for 'gitlab-ci-patterns' skill — GitLab CI Configuration Patterns
Validates .gitlab-ci.yml structure, stages ordering, manual deploys,
JUnit artifacts, rules vs only/except, and cache key configuration.
"""

import os
import sys

import pytest


class TestGitlabCiPatterns:
    """Verify GitLab CI configuration patterns via YAML analysis."""

    REPO_DIR = "/workspace/gitlabhq"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _root(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, *parts)

    def _load_ci(self):
        try:
            import yaml
        except ImportError:
            pytest.skip("pyyaml not available")
        path = self._root(".gitlab-ci.yml")
        if not os.path.isfile(path):
            pytest.skip(".gitlab-ci.yml not found")
        with open(path) as f:
            return yaml.safe_load(f)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_gitlab_ci_yml_exists(self):
        """.gitlab-ci.yml must exist at repo root."""
        path = self._root(".gitlab-ci.yml")
        assert os.path.isfile(path), ".gitlab-ci.yml not found"
        assert os.path.getsize(path) > 0

    def test_gitlab_ci_parses_as_yaml(self):
        """.gitlab-ci.yml must parse as valid YAML."""
        config = self._load_ci()
        assert isinstance(config, dict), "YAML did not parse as dict"

    def test_include_files_exist(self):
        """If .gitlab-ci.yml uses include:, referenced files must exist."""
        config = self._load_ci()
        includes = config.get("include", [])
        if isinstance(includes, list):
            for inc in includes:
                if isinstance(inc, dict) and "local" in inc:
                    path = self._root(inc["local"].lstrip("/"))
                    assert os.path.isfile(path), f"Include file missing: {inc['local']}"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_stages_include_build_test_deploy(self):
        """stages list must include build, test, deploy."""
        config = self._load_ci()
        stages = config.get("stages", [])
        for s in ("build", "test", "deploy"):
            assert any(s in stage for stage in stages), f"'{s}' stage not found"

    def test_production_deploy_when_manual(self):
        """Production deploy job must have when: manual."""
        config = self._load_ci()
        for name, job in config.items():
            if not isinstance(job, dict):
                continue
            env = job.get("environment")
            env_name = env if isinstance(env, str) else (env.get("name", "") if isinstance(env, dict) else "")
            if "production" in str(env_name).lower():
                assert job.get("when") == "manual", f"Job '{name}' not manual"
                return
        pytest.skip("No production environment job found")

    def test_junit_artifacts_on_test_jobs(self):
        """At least one test job must have artifacts.reports.junit."""
        config = self._load_ci()
        for name, job in config.items():
            if not isinstance(job, dict):
                continue
            reports = job.get("artifacts", {}).get("reports", {})
            if "junit" in reports:
                return
        pytest.fail("No JUnit artifact report found")

    def test_no_deprecated_only_except(self):
        """No job should use deprecated only/except keys."""
        config = self._load_ci()
        for name, job in config.items():
            if not isinstance(job, dict):
                continue
            assert "only" not in job, f"Deprecated 'only' in job '{name}'"
            assert "except" not in job, f"Deprecated 'except' in job '{name}'"

    def test_cache_key_has_ref_slug(self):
        """cache key must include $CI_COMMIT_REF_SLUG."""
        content = self._read_file(self._root(".gitlab-ci.yml"))
        if not content:
            pytest.skip(".gitlab-ci.yml not found")
        assert "$CI_COMMIT_REF_SLUG" in content, "Cache key missing $CI_COMMIT_REF_SLUG"

    # ── functional_check ─────────────────────────────────────────────────

    def test_stages_order(self):
        """build must come before test, test before deploy."""
        config = self._load_ci()
        stages = config.get("stages", [])
        def _find(keyword):
            for i, s in enumerate(stages):
                if keyword in s:
                    return i
            return -1
        bi, ti, di = _find("build"), _find("test"), _find("deploy")
        if bi >= 0 and ti >= 0:
            assert bi < ti, "build must come before test"
        if ti >= 0 and di >= 0:
            assert ti < di, "test must come before deploy"

    def test_production_job_manual_functional(self):
        """Programmatically find production job and verify when: manual."""
        config = self._load_ci()
        prod_jobs = []
        for name, job in config.items():
            if not isinstance(job, dict):
                continue
            env = job.get("environment")
            if isinstance(env, str) and "production" in env.lower():
                prod_jobs.append((name, job))
            elif isinstance(env, dict) and "production" in env.get("name", "").lower():
                prod_jobs.append((name, job))
        if not prod_jobs:
            pytest.skip("No production job found")
        for name, job in prod_jobs:
            assert job.get("when") == "manual", f"{name} not manual"

    def test_artifact_expiry_configured(self):
        """At least one job must have artifacts.expire_in."""
        config = self._load_ci()
        for name, job in config.items():
            if not isinstance(job, dict):
                continue
            expire = job.get("artifacts", {}).get("expire_in")
            if expire:
                return
        pytest.fail("No artifact expiry configured")

    def test_test_stage_jobs_have_reports(self):
        """All test-stage jobs must have artifacts.reports."""
        config = self._load_ci()
        for name, job in config.items():
            if not isinstance(job, dict):
                continue
            if job.get("stage") == "test":
                reports = job.get("artifacts", {}).get("reports", {})
                assert reports, f"Test job '{name}' missing artifacts.reports"
