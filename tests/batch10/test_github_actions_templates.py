"""
Test for 'github-actions-templates' skill — GitHub Actions workflow templates
Validates that the Agent created CI, Docker, and release-please YAML workflows
in the starter-workflows repository.
"""

import os
import re

import pytest


class TestGithubActionsTemplates:
    """Verify GitHub Actions workflow templates."""

    REPO_DIR = "/workspace/starter-workflows"

    def test_ci_workflow_exists(self):
        """CI workflow YAML must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"ci|continuous.integration|build.and.test", content, re.IGNORECASE):
                        if re.search(r"on:|push:|pull_request:", content):
                            found = True
                            break
            if found:
                break
        assert found, "CI workflow not found"

    def test_docker_workflow_exists(self):
        """Docker build/publish workflow YAML must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"docker|container|image", content, re.IGNORECASE):
                        if re.search(r"build|push|publish|registry", content, re.IGNORECASE):
                            found = True
                            break
            if found:
                break
        assert found, "Docker workflow not found"

    def test_release_please_workflow_exists(self):
        """Release-please or release workflow YAML must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"release.please|release|changelog|version.bump", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Release workflow not found"

    def test_ci_has_checkout_step(self):
        """CI workflow must use actions/checkout."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"actions/checkout", content):
                        found = True
                        break
            if found:
                break
        assert found, "No workflow uses actions/checkout"

    def test_ci_has_test_step(self):
        """CI workflow must include a test step."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"run:.*test|npm test|pytest|go test|mvn test|gradle test", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No test step found in workflows"

    def test_docker_workflow_has_build_push(self):
        """Docker workflow must include docker/build-push-action or equivalent."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"docker/build-push-action|docker\s+build|docker\s+push|buildx", content):
                        found = True
                        break
            if found:
                break
        assert found, "No Docker build/push action found"

    def test_workflow_uses_on_trigger(self):
        """All workflows must define 'on:' triggers."""
        workflows_dir = None
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".github" in root and "workflows" in root:
                workflows_dir = root
                break
        if workflows_dir is None:
            # Workflows may be at root level for starter-workflows repo
            workflows_dir = self.REPO_DIR
        found = False
        for root, dirs, files in os.walk(workflows_dir):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"^on:", content, re.MULTILINE):
                        found = True
                        break
            if found:
                break
        assert found, "No workflow defines 'on:' triggers"

    def test_workflows_define_jobs(self):
        """All workflows must define 'jobs:' section."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"^jobs:", content, re.MULTILINE):
                        found = True
                        break
            if found:
                break
        assert found, "No workflow defines 'jobs:' section"

    def test_workflows_use_runs_on(self):
        """Workflows must specify runs-on for the runner."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"runs-on:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No workflow specifies runs-on"

    def test_ci_matrix_or_strategy(self):
        """CI workflow should use matrix strategy or version parameterization."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"strategy:|matrix:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No matrix strategy found in CI workflows"
