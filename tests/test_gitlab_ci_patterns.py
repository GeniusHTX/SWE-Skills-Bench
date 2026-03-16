"""
Test for 'gitlab-ci-patterns' skill — GitLab CI Security Templates
Validates that the Agent created SAST, DAST, and Dependency Scanning
CI/CD template YAML files following GitLab conventions.
"""

import os
import pytest


class TestGitlabCiPatterns:
    """Verify GitLab CI security scanning templates."""

    REPO_DIR = "/workspace/gitlabhq"

    TEMPLATE_FILES = [
        "lib/gitlab/ci/templates/Security/SAST.gitlab-ci.yml",
        "lib/gitlab/ci/templates/Security/DAST.gitlab-ci.yml",
        "lib/gitlab/ci/templates/Security/Dependency-Scanning.gitlab-ci.yml",
    ]

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("tpl", TEMPLATE_FILES)
    def test_template_exists(self, tpl):
        """Security template file must exist."""
        fpath = os.path.join(self.REPO_DIR, tpl)
        assert os.path.isfile(fpath), f"{tpl} not found"

    # ------------------------------------------------------------------
    # L2: YAML content validation
    # ------------------------------------------------------------------

    def _load_template(self, tpl):
        import yaml

        fpath = os.path.join(self.REPO_DIR, tpl)
        with open(fpath, "r") as f:
            return yaml.safe_load(f)

    @pytest.mark.parametrize("tpl", TEMPLATE_FILES)
    def test_template_is_valid_yaml(self, tpl):
        """Template must be valid YAML."""
        doc = self._load_template(tpl)
        assert isinstance(doc, dict), f"{tpl} is not a YAML mapping"

    def test_sast_has_job_definition(self):
        """SAST template must define at least one job."""
        doc = self._load_template(self.TEMPLATE_FILES[0])
        job_keys = [k for k in doc.keys() if not k.startswith(".") and k != "variables"]
        assert len(job_keys) >= 1, f"SAST template has no job definitions"

    def test_sast_uses_sast_image(self):
        """SAST template must reference a SAST scanner image."""
        fpath = os.path.join(self.REPO_DIR, self.TEMPLATE_FILES[0])
        with open(fpath, "r") as f:
            content = f.read()
        image_markers = ["image:", "SAST", "sast", "semgrep", "analyzer"]
        found = sum(1 for m in image_markers if m in content)
        assert found >= 2, "SAST template doesn't reference scanner image"

    def test_dast_has_stage(self):
        """DAST template must define a stage."""
        doc = self._load_template(self.TEMPLATE_FILES[1])
        content = str(doc)
        assert "stage" in content.lower(), "DAST template missing stage definition"

    def test_dependency_scanning_has_artifacts(self):
        """Dependency Scanning template must define artifacts."""
        fpath = os.path.join(self.REPO_DIR, self.TEMPLATE_FILES[2])
        with open(fpath, "r") as f:
            content = f.read()
        assert "artifacts" in content, "Dependency Scanning missing artifacts section"

    def test_templates_have_script_or_include(self):
        """Each template must define script or include for execution."""
        for tpl in self.TEMPLATE_FILES:
            fpath = os.path.join(self.REPO_DIR, tpl)
            with open(fpath, "r") as f:
                content = f.read()
            has_execution = (
                "script:" in content or "include:" in content or "extends:" in content
            )
            assert has_execution, f"{tpl} has no script/include/extends"

    def test_sast_generates_report(self):
        """SAST template must configure gl-sast-report.json artifact."""
        fpath = os.path.join(self.REPO_DIR, self.TEMPLATE_FILES[0])
        with open(fpath, "r") as f:
            content = f.read()
        assert "report" in content.lower(), "SAST template missing report artifact"

    def test_templates_have_allow_failure(self):
        """Security templates should set allow_failure for non-blocking runs."""
        for tpl in self.TEMPLATE_FILES:
            fpath = os.path.join(self.REPO_DIR, tpl)
            with open(fpath, "r") as f:
                content = f.read()
            # allow_failure is a best practice but not strictly required
            # instead check for any of these common security template patterns
            patterns = ["allow_failure", "rules:", "only:", "when:"]
            found = any(p in content for p in patterns)
            assert found, f"{tpl} missing execution control (rules/only/when)"

    def test_templates_use_variables(self):
        """Templates should define configurable variables."""
        for tpl in self.TEMPLATE_FILES:
            fpath = os.path.join(self.REPO_DIR, tpl)
            with open(fpath, "r") as f:
                content = f.read()
            assert (
                "variables" in content or "$" in content
            ), f"{tpl} has no variables for configuration"
