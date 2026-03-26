"""
Test for 'gitlab-ci-patterns' skill — GitLab CI Security Templates
Validates that the Agent created SAST, DAST, and Dependency-Scanning
templates under lib/gitlab/ci/templates/Security/ with valid YAML,
correct GitLab CI job structure (rules, stages, artifacts, variables).
"""

import os
import re
import subprocess

import pytest
import yaml


class TestGitlabCiPatterns:
    """Verify GitLab CI Security pipeline templates."""

    REPO_DIR = "/workspace/gitlabhq"
    TEMPLATES_DIR = "lib/gitlab/ci/templates/Security"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    def _load_yaml(self, *parts):
        content = self._read(*parts)
        return yaml.safe_load(content)

    # ------------------------------------------------------------------
    # L1: Template files exist
    # ------------------------------------------------------------------

    def test_sast_template_exists(self):
        """SAST.gitlab-ci.yml must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.TEMPLATES_DIR, "SAST.gitlab-ci.yml")
        )

    def test_dast_template_exists(self):
        """DAST.gitlab-ci.yml must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.TEMPLATES_DIR, "DAST.gitlab-ci.yml")
        )

    def test_dependency_scanning_template_exists(self):
        """Dependency-Scanning.gitlab-ci.yml must exist."""
        assert os.path.isfile(
            os.path.join(
                self.REPO_DIR, self.TEMPLATES_DIR, "Dependency-Scanning.gitlab-ci.yml"
            )
        )

    # ------------------------------------------------------------------
    # L1: Valid YAML
    # ------------------------------------------------------------------

    def test_sast_valid_yaml(self):
        """SAST template must be valid YAML."""
        data = self._load_yaml(self.TEMPLATES_DIR, "SAST.gitlab-ci.yml")
        assert isinstance(data, dict), "SAST template is not a YAML mapping"

    def test_dast_valid_yaml(self):
        """DAST template must be valid YAML."""
        data = self._load_yaml(self.TEMPLATES_DIR, "DAST.gitlab-ci.yml")
        assert isinstance(data, dict), "DAST template is not a YAML mapping"

    def test_dependency_scanning_valid_yaml(self):
        """Dependency-Scanning template must be valid YAML."""
        data = self._load_yaml(self.TEMPLATES_DIR, "Dependency-Scanning.gitlab-ci.yml")
        assert isinstance(
            data, dict
        ), "Dependency-Scanning template is not a YAML mapping"

    # ------------------------------------------------------------------
    # L2: Job structure — stages
    # ------------------------------------------------------------------

    def test_sast_has_stage(self):
        """Each SAST job must declare a stage."""
        data = self._load_yaml(self.TEMPLATES_DIR, "SAST.gitlab-ci.yml")
        jobs = {
            k: v
            for k, v in data.items()
            if isinstance(v, dict) and not k.startswith(".")
        }
        for name, job in jobs.items():
            if "stage" in job:
                break
        else:
            # Accept top-level 'stages' key too
            assert "stages" in data, "SAST template has no stage declaration"

    def test_dast_has_stage(self):
        """DAST jobs must declare a stage."""
        data = self._load_yaml(self.TEMPLATES_DIR, "DAST.gitlab-ci.yml")
        content = self._read(self.TEMPLATES_DIR, "DAST.gitlab-ci.yml")
        assert re.search(r"stage:", content), "DAST template has no stage declaration"

    # ------------------------------------------------------------------
    # L2: Job structure — rules
    # ------------------------------------------------------------------

    def test_sast_has_rules_or_only(self):
        """SAST jobs must have rules or only/except to control execution."""
        content = self._read(self.TEMPLATES_DIR, "SAST.gitlab-ci.yml")
        assert re.search(
            r"(rules:|only:|except:)", content
        ), "SAST template missing rules/only/except"

    def test_dast_has_rules_or_only(self):
        """DAST jobs must have rules or only/except."""
        content = self._read(self.TEMPLATES_DIR, "DAST.gitlab-ci.yml")
        assert re.search(
            r"(rules:|only:|except:)", content
        ), "DAST template missing rules/only/except"

    # ------------------------------------------------------------------
    # L2: Job structure — artifacts
    # ------------------------------------------------------------------

    def test_sast_defines_artifacts(self):
        """SAST template should declare artifacts (reports)."""
        content = self._read(self.TEMPLATES_DIR, "SAST.gitlab-ci.yml")
        assert re.search(
            r"artifacts:", content
        ), "SAST template missing artifacts section"

    def test_dependency_scanning_defines_artifacts(self):
        """Dependency-Scanning template should declare artifacts."""
        content = self._read(self.TEMPLATES_DIR, "Dependency-Scanning.gitlab-ci.yml")
        assert re.search(
            r"artifacts:", content
        ), "Dependency-Scanning template missing artifacts section"

    # ------------------------------------------------------------------
    # L2: Job structure — variables
    # ------------------------------------------------------------------

    def test_sast_has_variables(self):
        """SAST template should define variables."""
        content = self._read(self.TEMPLATES_DIR, "SAST.gitlab-ci.yml")
        assert re.search(
            r"variables:", content
        ), "SAST template missing variables section"

    def test_dast_has_variables(self):
        """DAST template should define variables."""
        content = self._read(self.TEMPLATES_DIR, "DAST.gitlab-ci.yml")
        assert re.search(
            r"variables:", content
        ), "DAST template missing variables section"

    # ------------------------------------------------------------------
    # L2: Security report type
    # ------------------------------------------------------------------

    def test_sast_report_type(self):
        """SAST artifacts should reference sast report type."""
        content = self._read(self.TEMPLATES_DIR, "SAST.gitlab-ci.yml")
        assert re.search(
            r"sast", content, re.IGNORECASE
        ), "SAST template does not reference sast report"

    def test_dependency_scanning_report_type(self):
        """Dependency-Scanning artifacts should reference scanning report."""
        content = self._read(self.TEMPLATES_DIR, "Dependency-Scanning.gitlab-ci.yml")
        assert re.search(
            r"dependency.?scanning", content, re.IGNORECASE
        ), "Dependency-Scanning template missing report type reference"

    # ------------------------------------------------------------------
    # L2: Script sections exist
    # ------------------------------------------------------------------

    def test_templates_have_script(self):
        """Each template should define at least one script section."""
        for tpl in (
            "SAST.gitlab-ci.yml",
            "DAST.gitlab-ci.yml",
            "Dependency-Scanning.gitlab-ci.yml",
        ):
            content = self._read(self.TEMPLATES_DIR, tpl)
            assert re.search(r"script:", content), f"{tpl} missing script section"
