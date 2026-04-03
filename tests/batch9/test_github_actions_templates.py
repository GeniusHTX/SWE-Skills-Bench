"""
Test for 'github-actions-templates' skill — GitHub Actions Workflow Templates
Validates YAML workflow files for CI, release, deploy, and reusable workflows
including triggers, matrix strategy, caching, environment gates, and action versions.
"""

import glob
import os
import re
import subprocess
import sys

import pytest


class TestGithubActionsTemplates:
    """Verify GitHub Actions workflow YAML files for correctness and best practices."""

    REPO_DIR = "/workspace/starter-workflows"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _workflow_path(self, name: str) -> str:
        return os.path.join(self.REPO_DIR, ".github", "workflows", name)

    def _yaml_safe_load(self, path: str):
        """Load a YAML file via pyyaml; returns None on import/parse failure."""
        try:
            import yaml
        except ImportError:
            pytest.skip("pyyaml not installed")
        with open(path, "r") as fh:
            return yaml.safe_load(fh)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_ci_yml_exists(self):
        """ci.yml must exist as the main CI workflow file."""
        path = self._workflow_path("ci.yml")
        assert os.path.isfile(path), f"{path} does not exist"
        assert os.path.getsize(path) > 0

    def test_release_yml_exists(self):
        """release.yml must exist for semantic versioning and GitHub release."""
        path = self._workflow_path("release.yml")
        assert os.path.isfile(path), f"{path} does not exist"

    def test_deploy_yml_exists(self):
        """deploy.yml must exist for deployment workflow with environment gates."""
        path = self._workflow_path("deploy.yml")
        assert os.path.isfile(path), f"{path} does not exist"

    def test_reusable_test_yml_exists(self):
        """reusable-test.yml must exist as callable workflow with workflow_call trigger."""
        path = self._workflow_path("reusable-test.yml")
        assert os.path.isfile(path), f"{path} does not exist"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_ci_yml_has_push_and_pull_request_triggers(self):
        """ci.yml must define both push and pull_request triggers."""
        path = self._workflow_path("ci.yml")
        if not os.path.isfile(path):
            pytest.skip("ci.yml not found")
        config = self._yaml_safe_load(path)
        triggers = config.get("on") or config.get(True) or {}
        assert "push" in triggers, "ci.yml missing 'push' trigger"
        assert "pull_request" in triggers, "ci.yml missing 'pull_request' trigger"

    def test_ci_yml_matrix_strategy_defined(self):
        """CI workflow must define matrix strategy with os and version arrays."""
        path = self._workflow_path("ci.yml")
        if not os.path.isfile(path):
            pytest.skip("ci.yml not found")
        config = self._yaml_safe_load(path)
        jobs = config.get("jobs", {})
        found = False
        for job in jobs.values():
            matrix = (job.get("strategy") or {}).get("matrix")
            if matrix and "os" in matrix:
                found = True
                assert isinstance(matrix["os"], list) and len(matrix["os"]) >= 2
                break
        assert found, "No job with strategy.matrix.os found in ci.yml"

    def test_release_yml_triggers_on_version_tags(self):
        """release.yml must trigger only on push of version tags matching v*."""
        path = self._workflow_path("release.yml")
        if not os.path.isfile(path):
            pytest.skip("release.yml not found")
        config = self._yaml_safe_load(path)
        triggers = config.get("on") or config.get(True) or {}
        push = triggers.get("push", {})
        tags = push.get("tags", [])
        assert any(
            t.startswith("v") for t in tags
        ), f"release.yml push tags do not contain a v* pattern: {tags}"

    def test_deploy_yml_production_environment(self):
        """deploy.yml must have a job with environment name 'production'."""
        path = self._workflow_path("deploy.yml")
        if not os.path.isfile(path):
            pytest.skip("deploy.yml not found")
        config = self._yaml_safe_load(path)
        jobs = config.get("jobs", {})
        found = False
        for job in jobs.values():
            env = job.get("environment", {})
            env_name = env.get("name") if isinstance(env, dict) else env
            if env_name == "production":
                found = True
                break
        assert found, "No job with environment 'production' in deploy.yml"

    def test_cache_key_includes_lockfile_hash(self):
        """ci.yml must use hashFiles() in a cache key for proper invalidation."""
        path = self._workflow_path("ci.yml")
        if not os.path.isfile(path):
            pytest.skip("ci.yml not found")
        content = self._read_file(path)
        assert "hashFiles(" in content, "ci.yml does not contain hashFiles() in cache key"

    # ── functional_check ─────────────────────────────────────────────────

    def test_all_workflow_yamls_parse_without_errors(self):
        """All .github/workflows/*.yml files must parse as valid YAML."""
        try:
            import yaml
        except ImportError:
            pytest.skip("pyyaml not installed")
        pattern = os.path.join(self.REPO_DIR, ".github", "workflows", "*.yml")
        files = glob.glob(pattern)
        assert len(files) >= 1, "No workflow YAML files found"
        for f in files:
            with open(f, "r") as fh:
                try:
                    yaml.safe_load(fh)
                except yaml.YAMLError as exc:
                    pytest.fail(f"YAML parse error in {f}: {exc}")

    def test_reusable_workflow_has_workflow_call_trigger(self):
        """reusable-test.yml must have on.workflow_call trigger."""
        path = self._workflow_path("reusable-test.yml")
        if not os.path.isfile(path):
            pytest.skip("reusable-test.yml not found")
        config = self._yaml_safe_load(path)
        triggers = config.get("on") or config.get(True) or {}
        assert "workflow_call" in triggers, "reusable-test.yml missing workflow_call trigger"

    def test_deprecated_checkout_action_not_used(self):
        """No workflow file should use deprecated actions/checkout@v1 or @v2."""
        pattern = os.path.join(self.REPO_DIR, ".github", "workflows", "*.yml")
        files = glob.glob(pattern)
        assert len(files) >= 1, "No workflow YAML files found"
        deprecated = re.compile(r"actions/checkout@v[12]\b")
        for f in files:
            content = self._read_file(f)
            match = deprecated.search(content)
            assert match is None, f"Deprecated checkout action in {f}: {match.group()}"

    def test_matrix_os_is_list_type(self):
        """Matrix os entry must be a list, even with a single element."""
        path = self._workflow_path("ci.yml")
        if not os.path.isfile(path):
            pytest.skip("ci.yml not found")
        config = self._yaml_safe_load(path)
        jobs = config.get("jobs", {})
        for job in jobs.values():
            matrix = (job.get("strategy") or {}).get("matrix")
            if matrix and "os" in matrix:
                assert isinstance(matrix["os"], list), "matrix.os must be a list type"
                break
