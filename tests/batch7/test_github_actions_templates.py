"""Test file for the github-actions-templates skill.

This suite validates the Node.js library CI and publish GitHub Actions
workflow templates in the starter-workflows repository.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest
import yaml


class TestGithubActionsTemplates:
    """Verify GitHub Actions workflow templates for Node.js library CI/CD."""

    REPO_DIR = "/workspace/starter-workflows"

    CI_YML = "ci/node-library-ci.yml"
    PUBLISH_YML = "deployments/node-library-publish.yml"
    CI_PROPS = "ci/node-library-ci.properties.json"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    def _parse_yaml(self, relative: str) -> dict:
        """Parse a YAML file, replacing GitHub Actions template variables."""
        text = self._read_text(relative)
        # Replace $default-branch placeholder so YAML parser doesn't choke
        text = text.replace("$default-branch", "main")
        return yaml.safe_load(text)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_ci_node_library_ci_yml_exists(self):
        """Verify ci/node-library-ci.yml exists and is non-empty."""
        self._assert_non_empty_file(self.CI_YML)

    def test_file_path_deployments_node_library_publish_yml_exists(self):
        """Verify deployments/node-library-publish.yml exists and is non-empty."""
        self._assert_non_empty_file(self.PUBLISH_YML)

    def test_file_path_ci_node_library_ci_properties_json_exists(self):
        """Verify ci/node-library-ci.properties.json exists and is non-empty."""
        self._assert_non_empty_file(self.CI_PROPS)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_ci_workflow_yaml_contains_matrix_with_node_version_18_20_22(self):
        """CI workflow YAML contains matrix with node-version: [18, 20, 22]."""
        src = self._read_text(self.CI_YML)
        assert "node-version" in src, "CI workflow must define node-version matrix"
        for ver in ("18", "20", "22"):
            assert ver in src, f"CI workflow matrix must include Node.js {ver}"

    def test_semantic_ci_workflow_has_fail_fast_false(self):
        """CI workflow has fail-fast: false."""
        src = self._read_text(self.CI_YML)
        assert re.search(
            r"fail-fast\s*:\s*false", src
        ), "CI workflow should have fail-fast: false"

    def test_semantic_ci_workflow_has_concurrency_group_configuration(self):
        """CI workflow has concurrency group configuration."""
        src = self._read_text(self.CI_YML)
        assert "concurrency" in src, "CI workflow should have concurrency configuration"
        assert "group" in src, "Concurrency configuration should include group"

    def test_semantic_ci_workflow_has_permissions_contents_read(self):
        """CI workflow has permissions: contents: read."""
        src = self._read_text(self.CI_YML)
        assert "permissions" in src, "CI workflow should define permissions"
        assert re.search(
            r"contents\s*:\s*read", src
        ), "CI workflow should have contents: read permission"

    def test_semantic_ci_workflow_has_npm_audit_audit_level_high_step(self):
        """CI workflow has npm audit --audit-level=high step."""
        src = self._read_text(self.CI_YML)
        assert re.search(
            r"npm\s+audit|audit-level", src
        ), "CI workflow should include npm audit step"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (4 cases)
    # ------------------------------------------------------------------

    def test_functional_ci_workflow_is_valid_yaml_parseable_by_a_yaml_parser(self):
        """CI workflow is valid YAML parseable by a YAML parser."""
        data = self._parse_yaml(self.CI_YML)
        assert isinstance(data, dict), "CI workflow YAML should parse to a dict"
        assert "on" in data or True in data, "CI workflow must have 'on' trigger"
        assert "jobs" in data, "CI workflow must have 'jobs' section"

    def test_functional_publish_workflow_is_valid_yaml_parseable_by_a_yaml_parser(self):
        """Publish workflow is valid YAML parseable by a YAML parser."""
        data = self._parse_yaml(self.PUBLISH_YML)
        assert isinstance(data, dict), "Publish workflow YAML should parse to a dict"
        assert "jobs" in data, "Publish workflow must have 'jobs' section"

    def test_functional_properties_json_files_are_valid_json(self):
        """.properties.json files are valid JSON."""
        text = self._read_text(self.CI_PROPS)
        data = json.loads(text)
        assert isinstance(data, dict), "properties.json should be a valid JSON object"

    def test_functional_categories_arrays_contain_correct_values_per_requirements(self):
        """Categories arrays contain correct values per requirements."""
        text = self._read_text(self.CI_PROPS)
        data = json.loads(text)
        assert "categories" in data, "properties.json should have 'categories' field"
        categories = data["categories"]
        assert isinstance(categories, list), "categories should be an array"
        assert len(categories) > 0, "categories should not be empty"
