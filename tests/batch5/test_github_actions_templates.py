"""
Test for 'github-actions-templates' skill — GitHub Actions Workflow Templates
Validates CI/CD workflow YAMLs with push triggers, staging→production gates,
reusable workflow_call, and no hardcoded secrets.
"""

import os
import re

import pytest

try:
    import yaml
except ImportError:
    yaml = None


class TestGithubActionsTemplates:
    """Verify GitHub Actions workflow template patterns."""

    REPO_DIR = "/workspace/starter-workflows"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_workflow_yaml_files_exist(self):
        """Verify at least 3 workflow YAML files exist."""
        yml_files = self._find_workflow_files()
        assert (
            len(yml_files) >= 3
        ), f"Expected ≥3 workflow YAML files, found {len(yml_files)}"

    def test_ci_workflow_exists(self):
        """Verify a CI workflow file exists."""
        yml_files = self._find_workflow_files()
        for fpath in yml_files:
            name = os.path.basename(fpath).lower()
            content = self._read(fpath)
            if "ci" in name or re.search(r"(test|lint|build)", name):
                return
            if "push" in content and ("test" in content or "build" in content):
                return
        pytest.fail("No CI workflow found")

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_ci_has_push_trigger(self):
        """Verify CI workflow triggers on push."""
        yml_files = self._find_workflow_files()
        assert yml_files, "No workflow files"
        for fpath in yml_files:
            content = self._read(fpath)
            if re.search(r"on:\s*\n\s*push:|on:\s*\[?push", content):
                return
        pytest.fail("No workflow triggers on push")

    def test_cd_staging_production_gate(self):
        """Verify CD workflow has staging→production deployment gate."""
        yml_files = self._find_workflow_files()
        for fpath in yml_files:
            content = self._read(fpath)
            if "staging" in content.lower() and "production" in content.lower():
                return
            if re.search(r"environment:\s*(staging|production)", content):
                return
        pytest.fail("No staging→production deployment gate found")

    def test_reusable_workflow_call(self):
        """Verify at least one reusable workflow uses workflow_call trigger."""
        yml_files = self._find_workflow_files()
        for fpath in yml_files:
            content = self._read(fpath)
            if "workflow_call" in content:
                return
        pytest.fail("No reusable workflow with workflow_call found")

    def test_no_hardcoded_secrets(self):
        """Verify no hardcoded secrets (should use ${{ secrets.* }})."""
        yml_files = self._find_workflow_files()
        assert yml_files, "No workflow files"
        for fpath in yml_files:
            content = self._read(fpath)
            # Check for hardcoded tokens (simple heuristic)
            if re.search(r"(ghp_[A-Za-z0-9]{36}|github_pat_|sk-[a-z]{20,})", content):
                pytest.fail(f"Hardcoded secret found in {os.path.basename(fpath)}")

    # ── functional_check ────────────────────────────────────────────────────

    def test_workflow_yaml_valid(self):
        """Verify workflow YAML files parse correctly."""
        if yaml is None:
            pytest.skip("PyYAML not available")
        yml_files = self._find_workflow_files()
        assert yml_files, "No workflow files"
        for fpath in yml_files:
            with open(fpath, "r") as fh:
                try:
                    data = yaml.safe_load(fh)
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {os.path.basename(fpath)}: {e}")
            assert data is not None, f"Empty YAML: {os.path.basename(fpath)}"

    def test_workflows_have_required_keys(self):
        """Verify workflows have 'name', 'on', and 'jobs' keys."""
        if yaml is None:
            pytest.skip("PyYAML not available")
        yml_files = self._find_workflow_files()
        assert yml_files, "No workflow files"
        for fpath in yml_files:
            with open(fpath, "r") as fh:
                data = yaml.safe_load(fh)
            if data is None:
                continue
            # 'on' may be parsed as True for bare 'on:'
            has_on = "on" in data or True in data
            assert has_on, f"Missing 'on' trigger in {os.path.basename(fpath)}"
            assert "jobs" in data, f"Missing 'jobs' in {os.path.basename(fpath)}"

    def test_secrets_use_expression_syntax(self):
        """Verify secrets reference uses ${{ secrets.* }} syntax."""
        yml_files = self._find_workflow_files()
        has_secrets_ref = False
        for fpath in yml_files:
            content = self._read(fpath)
            if re.search(r"\$\{\{\s*secrets\.", content):
                has_secrets_ref = True
                break
        # It's ok if no secrets are referenced at all
        if not has_secrets_ref:
            for fpath in yml_files:
                content = self._read(fpath)
                if "secret" in content.lower() or "token" in content.lower():
                    pytest.fail("Secret/token referenced without ${{ secrets.* }}")

    def test_jobs_have_runs_on(self):
        """Verify all jobs specify runs-on."""
        if yaml is None:
            pytest.skip("PyYAML not available")
        yml_files = self._find_workflow_files()
        for fpath in yml_files:
            with open(fpath, "r") as fh:
                data = yaml.safe_load(fh)
            if data is None or "jobs" not in data:
                continue
            for job_name, job_def in data["jobs"].items():
                if isinstance(job_def, dict):
                    assert (
                        "runs-on" in job_def or "uses" in job_def
                    ), f"Job '{job_name}' in {os.path.basename(fpath)} missing runs-on"

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_workflow_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".yml") or f.endswith(".yaml"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
