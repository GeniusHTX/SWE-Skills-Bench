"""
Tests for gitlab-ci-patterns skill.
Validates GitLab CI configuration in gitlabhq repository.
"""

import os
import subprocess
import re
import pytest

REPO_DIR = "/workspace/gitlabhq"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


def _run(cmd: str, cwd: str = REPO_DIR, timeout: int = 60):
    return subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


class TestGitlabCiPatterns:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_gitlab_ci_yml_exists(self):
        """.gitlab-ci.yml must exist and be non-empty."""
        rel = ".gitlab-ci.yml"
        assert os.path.isfile(_path(rel)), ".gitlab-ci.yml not found"
        assert os.path.getsize(_path(rel)) > 0, ".gitlab-ci.yml is empty"

    def test_dynamic_pipeline_files_exist(self):
        """generate-pipeline.rb and ci/templates/build.yml must exist."""
        for rel in [
            "ci/dynamic/generate-pipeline.rb",
            "ci/templates/build.yml",
        ]:
            assert os.path.isfile(_path(rel)), f"{rel} not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_gitlab_ci_defines_required_stages(self):
        """.gitlab-ci.yml must define build, test, security, deploy-staging, deploy-production stages."""
        content = _read(".gitlab-ci.yml")
        for stage in [
            "build",
            "test",
            "security",
            "deploy-staging",
            "deploy-production",
        ]:
            assert (
                stage in content
            ), f"Required stage '{stage}' not found in .gitlab-ci.yml"

    def test_docker_dind_service_defined(self):
        """docker:24-dind service must be defined for Docker-in-Docker builds."""
        content = _read(".gitlab-ci.yml")
        assert (
            "docker:24-dind" in content or "docker:dind" in content
        ), "Docker-in-Docker service not found in .gitlab-ci.yml"

    def test_rspec_uses_parallel_4(self):
        """rspec job must use parallel: 4 for parallel test execution."""
        content = _read(".gitlab-ci.yml")
        assert "parallel: 4" in content, "rspec job must define 'parallel: 4'"

    def test_production_deploy_requires_manual_trigger(self):
        """deploy-production job must have when: manual gate."""
        content = _read(".gitlab-ci.yml")
        assert (
            "when: manual" in content
        ), "deploy-production job must include 'when: manual'"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_gitlab_ci_yaml_is_valid(self):
        """.gitlab-ci.yml must parse as valid YAML."""
        import yaml

        content = _read(".gitlab-ci.yml")
        data = yaml.safe_load(content)
        assert data is not None, ".gitlab-ci.yml parsed as empty"

    def test_ruby_pipeline_generator_has_valid_syntax(self):
        """generate-pipeline.rb must pass ruby -c syntax check."""
        result = _run("ruby -c ci/dynamic/generate-pipeline.rb")
        if result.returncode != 0 and "command not found" in result.stderr.lower():
            pytest.skip("ruby not available")
        assert result.returncode == 0, f"Ruby syntax error:\n{result.stderr}"
        assert "Syntax OK" in result.stdout

    def test_build_template_yaml_is_valid(self):
        """ci/templates/build.yml must parse as valid YAML."""
        import yaml

        content = _read("ci/templates/build.yml")
        data = yaml.safe_load(content)
        assert data is not None, "ci/templates/build.yml parsed as empty"

    def test_gitlab_ci_uses_include_for_templates(self):
        """.gitlab-ci.yml must use include: to reference CI templates."""
        content = _read(".gitlab-ci.yml")
        assert (
            "include:" in content
        ), ".gitlab-ci.yml must use 'include:' directive to reference shared templates"

    def test_all_job_stages_are_declared(self):
        """Every job stage: value must appear in the global stages: list."""
        import yaml

        content = _read(".gitlab-ci.yml")
        data = yaml.safe_load(content)
        global_stages = data.get("stages", [])
        for job_name, job_def in data.items():
            if isinstance(job_def, dict) and "stage" in job_def:
                stage = job_def["stage"]
                assert (
                    stage in global_stages
                ), f"Job '{job_name}' uses stage '{stage}' not in global stages list"

    def test_no_raw_credentials_in_ci_config(self):
        """Credential values in .gitlab-ci.yml must use $VAR substitution."""
        content = _read(".gitlab-ci.yml")
        # Find lines with credential keywords and verify they use variable references
        cred_lines = [
            line
            for line in content.splitlines()
            if re.search(r"(?i)(password|token|secret)\s*:", line)
        ]
        for line in cred_lines:
            value = line.split(":", 1)[-1].strip()
            assert (
                value.startswith("$") or value.startswith('"$') or value == ""
            ), f"Hardcoded credential found: {line.strip()}"
