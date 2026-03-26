"""
Test for 'github-actions-templates' skill — Python CI Workflow Template
Validates that the Agent created a GitHub Actions workflow for Python pytest
with triggers, matrix strategy, caching, and CI best practices.
"""

import os
import re

import yaml
import pytest


class TestGithubActionsTemplates:
    """Verify Python pytest CI workflow template."""

    REPO_DIR = "/workspace/starter-workflows"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    def _load_workflow(self):
        text = self._read("ci", "python-pytest.yml")
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as exc:
            pytest.fail(f"Invalid YAML: {exc}")

    # ------------------------------------------------------------------
    # L1: File existence and YAML validity
    # ------------------------------------------------------------------

    def test_workflow_file_exists(self):
        """ci/python-pytest.yml must exist."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, "ci", "python-pytest.yml"))

    def test_valid_yaml(self):
        """Workflow file must be valid YAML."""
        self._load_workflow()

    # ------------------------------------------------------------------
    # L1: Trigger configuration
    # ------------------------------------------------------------------

    def test_triggers_on_push(self):
        """Workflow must trigger on push to main."""
        data = self._load_workflow()
        on = data.get("on", data.get(True, {}))
        if isinstance(on, str):
            assert on == "push"
            return
        push_config = on.get("push", {})
        branches = push_config.get("branches", [])
        assert (
            "main" in branches or "master" in branches
        ), "Workflow does not trigger on push to main"

    def test_triggers_on_pull_request(self):
        """Workflow must trigger on pull requests targeting main."""
        data = self._load_workflow()
        on = data.get("on", data.get(True, {}))
        if isinstance(on, str):
            pytest.skip("Simple string trigger")
        pr_config = on.get("pull_request", {})
        assert pr_config is not None, "Workflow does not trigger on pull_request"

    # ------------------------------------------------------------------
    # L2: Job structure
    # ------------------------------------------------------------------

    def test_has_test_job(self):
        """Workflow must define a test job."""
        data = self._load_workflow()
        jobs = data.get("jobs", {})
        assert len(jobs) >= 1, "No jobs defined"

    def test_runs_on_ubuntu(self):
        """Test job must run on ubuntu-latest."""
        data = self._load_workflow()
        jobs = data.get("jobs", {})
        for job in jobs.values():
            runs_on = str(job.get("runs-on", ""))
            if "ubuntu" in runs_on:
                return
        pytest.fail("No job runs on ubuntu")

    # ------------------------------------------------------------------
    # L2: Matrix strategy
    # ------------------------------------------------------------------

    def test_matrix_python_versions(self):
        """Job must use matrix strategy with multiple Python versions."""
        data = self._load_workflow()
        jobs = data.get("jobs", {})
        for job in jobs.values():
            strategy = job.get("strategy", {})
            matrix = strategy.get("matrix", {})
            versions = matrix.get("python-version", matrix.get("python", []))
            if len(versions) >= 2:
                return
        pytest.fail("No matrix strategy with multiple Python versions")

    # ------------------------------------------------------------------
    # L2: Steps
    # ------------------------------------------------------------------

    def test_has_checkout_step(self):
        """Job must include checkout step."""
        data = self._load_workflow()
        text = self._read("ci", "python-pytest.yml")
        assert re.search(r"actions/checkout", text), "No checkout step found"

    def test_has_python_setup_step(self):
        """Job must include Python setup step."""
        text = self._read("ci", "python-pytest.yml")
        assert re.search(r"actions/setup-python", text), "No setup-python step found"

    def test_has_pytest_step(self):
        """Job must run pytest."""
        text = self._read("ci", "python-pytest.yml")
        assert re.search(r"pytest", text), "No pytest step found"

    # ------------------------------------------------------------------
    # L2: Best practices
    # ------------------------------------------------------------------

    def test_pinned_action_versions(self):
        """Actions should be pinned to specific versions."""
        text = self._read("ci", "python-pytest.yml")
        uses_lines = re.findall(r"uses:\s*(\S+)", text)
        for use in uses_lines:
            assert "@" in use, f"Action not pinned: {use}"

    def test_pip_caching(self):
        """Job should cache pip dependencies."""
        text = self._read("ci", "python-pytest.yml")
        patterns = [
            r"cache.*pip",
            r"actions/cache",
            r"cache:\s*pip",
            r"setup-python.*cache",
        ]
        assert any(
            re.search(p, text, re.IGNORECASE) for p in patterns
        ), "No pip caching configured"

    def test_has_permissions(self):
        """Workflow should set permissions."""
        text = self._read("ci", "python-pytest.yml")
        assert re.search(r"permissions", text), "Workflow does not set permissions"
