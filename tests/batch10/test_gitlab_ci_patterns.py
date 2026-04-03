"""
Test for 'gitlab-ci-patterns' skill — GitLab CI 5-stage pipeline
Validates that the Agent created a multi-stage GitLab CI/CD pipeline YAML
for the gitlabhq project.
"""

import os
import re

import pytest


class TestGitlabCiPatterns:
    """Verify GitLab CI pipeline configuration."""

    REPO_DIR = "/workspace/gitlabhq"

    def test_gitlab_ci_yml_exists(self):
        """.gitlab-ci.yml must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".gitlab-ci.yml" in files:
                found = True
                break
        assert found, ".gitlab-ci.yml not found"

    def test_stages_defined(self):
        """Pipeline must define stages."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".gitlab-ci.yml" in files:
                path = os.path.join(root, ".gitlab-ci.yml")
                with open(path, "r", errors="ignore") as fh:
                    content = fh.read()
                if re.search(r"^stages:", content, re.MULTILINE):
                    found = True
                break
        assert found, "No stages defined in .gitlab-ci.yml"

    def test_build_stage_exists(self):
        """Build stage must be present."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".gitlab-ci.yml" in files:
                path = os.path.join(root, ".gitlab-ci.yml")
                with open(path, "r", errors="ignore") as fh:
                    content = fh.read()
                if re.search(r"build", content, re.IGNORECASE):
                    found = True
                break
        assert found, "Build stage not found"

    def test_test_stage_exists(self):
        """Test stage must be present."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".gitlab-ci.yml" in files:
                path = os.path.join(root, ".gitlab-ci.yml")
                with open(path, "r", errors="ignore") as fh:
                    content = fh.read()
                if re.search(r"test", content, re.IGNORECASE):
                    found = True
                break
        assert found, "Test stage not found"

    def test_deploy_stage_exists(self):
        """Deploy stage must be present."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".gitlab-ci.yml" in files:
                path = os.path.join(root, ".gitlab-ci.yml")
                with open(path, "r", errors="ignore") as fh:
                    content = fh.read()
                if re.search(r"deploy", content, re.IGNORECASE):
                    found = True
                break
        assert found, "Deploy stage not found"

    def test_jobs_have_stage_assignment(self):
        """Jobs must be assigned to stages."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".gitlab-ci.yml" in files:
                path = os.path.join(root, ".gitlab-ci.yml")
                with open(path, "r", errors="ignore") as fh:
                    content = fh.read()
                if re.search(r"stage:", content):
                    found = True
                break
        assert found, "No jobs have stage assignment"

    def test_jobs_have_script(self):
        """Jobs must have script sections."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".gitlab-ci.yml" in files:
                path = os.path.join(root, ".gitlab-ci.yml")
                with open(path, "r", errors="ignore") as fh:
                    content = fh.read()
                if re.search(r"script:", content):
                    found = True
                break
        assert found, "No jobs have script sections"

    def test_pipeline_uses_image(self):
        """Pipeline should specify a Docker image."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".gitlab-ci.yml" in files:
                path = os.path.join(root, ".gitlab-ci.yml")
                with open(path, "r", errors="ignore") as fh:
                    content = fh.read()
                if re.search(r"image:", content):
                    found = True
                break
        assert found, "No Docker image specified"

    def test_pipeline_has_five_stages(self):
        """Pipeline should have approximately 5 stages."""
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".gitlab-ci.yml" in files:
                path = os.path.join(root, ".gitlab-ci.yml")
                with open(path, "r", errors="ignore") as fh:
                    content = fh.read()
                match = re.search(r"^stages:\s*\n((?:\s+-\s+\S+\n?)+)", content, re.MULTILINE)
                if match:
                    stage_lines = re.findall(r"^\s+-\s+(\S+)", match.group(1), re.MULTILINE)
                    assert len(stage_lines) >= 3, f"Expected at least 3 stages, got {len(stage_lines)}"
                    return
                break
        pytest.fail("Could not parse stages from .gitlab-ci.yml")

    def test_pipeline_uses_rules_or_only(self):
        """Pipeline jobs should use rules: or only: for conditional execution."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".gitlab-ci.yml" in files:
                path = os.path.join(root, ".gitlab-ci.yml")
                with open(path, "r", errors="ignore") as fh:
                    content = fh.read()
                if re.search(r"rules:|only:|except:|when:", content):
                    found = True
                break
        assert found, "No conditional rules found in pipeline"
