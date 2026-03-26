"""
Tests for github-actions-templates skill.
Validates GitHub Actions workflow YAML files in starter-workflows repository.
"""

import os
import subprocess
import pytest

REPO_DIR = "/workspace/starter-workflows"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


def _run(cmd: str, cwd: str = REPO_DIR, timeout: int = 30):
    return subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


class TestGithubActionsTemplates:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_node_ci_workflow_file_exists(self):
        """node-ci.yml must exist and be non-empty."""
        rel = ".github/workflows/node-ci.yml"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "node-ci.yml is empty"

    def test_docker_and_terraform_workflow_files_exist(self):
        """docker-build-push.yml and terraform-plan-apply.yml must exist."""
        for rel in [
            ".github/workflows/docker-build-push.yml",
            ".github/workflows/terraform-plan-apply.yml",
        ]:
            assert os.path.isfile(_path(rel)), f"{rel} not found"

    def test_node_ci_has_workflow_call_trigger(self):
        """node-ci.yml must have workflow_call trigger with inputs."""
        content = _read(".github/workflows/node-ci.yml")
        assert (
            "workflow_call" in content
        ), "node-ci.yml must define workflow_call: trigger"
        assert (
            "inputs:" in content
        ), "node-ci.yml must define inputs: under workflow_call"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_node_ci_uses_matrix_strategy(self):
        """node-ci.yml must use matrix strategy for multi-version testing."""
        content = _read(".github/workflows/node-ci.yml")
        assert "matrix:" in content, "node-ci.yml must define matrix: strategy"
        assert "strategy:" in content, "node-ci.yml must include strategy: block"

    def test_workflows_have_concurrency_cancel_in_progress(self):
        """node-ci.yml must define concurrency with cancel-in-progress: true."""
        content = _read(".github/workflows/node-ci.yml")
        assert "concurrency:" in content, "node-ci.yml must define concurrency: section"
        assert (
            "cancel-in-progress: true" in content
        ), "node-ci.yml must set cancel-in-progress: true"

    def test_docker_workflow_uses_metadata_action(self):
        """docker-build-push.yml must use docker/metadata-action for tagging."""
        content = _read(".github/workflows/docker-build-push.yml")
        assert (
            "docker/metadata-action" in content
        ), "docker-build-push.yml must reference docker/metadata-action"

    def test_terraform_workflow_has_separate_plan_and_apply(self):
        """terraform-plan-apply.yml must define separate plan and apply jobs."""
        content = _read(".github/workflows/terraform-plan-apply.yml")
        assert (
            "plan" in content.lower()
        ), "terraform-plan-apply.yml must define a 'plan' job"
        assert (
            "apply" in content.lower()
        ), "terraform-plan-apply.yml must define an 'apply' job"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_node_ci_yaml_is_valid(self):
        """node-ci.yml must parse as valid YAML."""
        import yaml

        content = _read(".github/workflows/node-ci.yml")
        data = yaml.safe_load(content)
        assert data is not None, "node-ci.yml parsed as empty"

    def test_docker_workflow_yaml_is_valid(self):
        """docker-build-push.yml must parse as valid YAML."""
        import yaml

        content = _read(".github/workflows/docker-build-push.yml")
        data = yaml.safe_load(content)
        assert data is not None, "docker-build-push.yml parsed as empty"

    def test_docker_workflow_has_id_token_write_permission(self):
        """docker-build-push.yml must grant id-token: write for OIDC auth."""
        content = _read(".github/workflows/docker-build-push.yml")
        assert (
            "id-token: write" in content
        ), "docker-build-push.yml must set id-token: write permission for OIDC"

    def test_malformed_yaml_is_detected(self):
        """Python yaml.safe_load must raise YAMLError on invalid YAML."""
        import yaml

        malformed = "invalid: yaml: : :"
        with pytest.raises(yaml.YAMLError):
            yaml.safe_load(malformed)

    def test_node_ci_does_not_use_deprecated_v1_actions(self):
        """node-ci.yml must not use @v1 or @v2 for checkout/setup-node actions."""
        content = _read(".github/workflows/node-ci.yml")
        import re

        deprecated = re.findall(r"actions/(?:checkout|setup-node)@v[12]\b", content)
        assert len(deprecated) == 0, f"Deprecated action versions found: {deprecated}"
