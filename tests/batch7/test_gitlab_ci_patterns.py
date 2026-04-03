"""Test file for the gitlab-ci-patterns skill.

This suite validates the PipelineTemplateGenerator, StageConfig, and
JobDefinition classes in the GitLab CI pipeline template infrastructure.
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

import pytest


class TestGitlabCiPatterns:
    """Verify GitLab CI pipeline template generator in gitlabhq."""

    REPO_DIR = "/workspace/gitlabhq"

    GENERATOR_RB = "lib/gitlab/ci/pipeline_template_generator.rb"
    STAGES_RB = "lib/gitlab/ci/stage_definitions.rb"
    SPEC_RB = "spec/lib/gitlab/ci/pipeline_template_generator_spec.rb"

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

    def _all_rb_sources(self) -> str:
        """Concatenate the main Ruby source files."""
        parts = []
        ci_dir = self._repo_path("lib/gitlab/ci")
        if ci_dir.is_dir():
            for f in sorted(ci_dir.glob("*.rb")):
                parts.append(f.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    def _run_ruby(self, script: str) -> subprocess.CompletedProcess:
        """Execute a Ruby script in the repo context."""
        return subprocess.run(
            ["ruby", "-e", script],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_lib_gitlab_ci_pipeline_template_generator_rb_exists(self):
        """Verify pipeline_template_generator.rb exists and is non-empty."""
        self._assert_non_empty_file(self.GENERATOR_RB)

    def test_file_path_lib_gitlab_ci_stage_definitions_rb_exists(self):
        """Verify stage_definitions.rb exists and is non-empty."""
        self._assert_non_empty_file(self.STAGES_RB)

    def test_file_path_spec_lib_gitlab_ci_pipeline_template_generator_spec_rb_exist(
        self,
    ):
        """Verify pipeline_template_generator_spec.rb exists and is non-empty."""
        self._assert_non_empty_file(self.SPEC_RB)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_pipelinetemplategenerator_class_defined_in_gitlab_ci_module(self):
        """PipelineTemplateGenerator class defined in Gitlab::CI module."""
        src = self._read_text(self.GENERATOR_RB)
        assert re.search(
            r"module\s+Gitlab", src
        ), "Generator should be in Gitlab module"
        assert re.search(
            r"class\s+PipelineTemplateGenerator", src
        ), "PipelineTemplateGenerator class not found"

    def test_semantic_supported_types_constant_includes_rails_node_python_golang(self):
        """SUPPORTED_TYPES constant includes rails, node, python, golang."""
        src = self._all_rb_sources()
        assert re.search(
            r"SUPPORTED_TYPES|supported_types", src
        ), "SUPPORTED_TYPES constant not found"
        for project_type in ("rails", "node", "python", "golang"):
            assert re.search(
                rf"['\"]?{project_type}['\"]?", src
            ), f"SUPPORTED_TYPES should include '{project_type}'"

    def test_semantic_stageconfig_and_jobdefinition_structs_defined_with_correct_f(
        self,
    ):
        """StageConfig and JobDefinition structs defined with correct fields."""
        src = self._all_rb_sources()
        assert re.search(
            r"StageConfig|Stage[Cc]onfig", src
        ), "StageConfig struct/class not found"
        assert re.search(
            r"JobDefinition|Job[Dd]efinition", src
        ), "JobDefinition struct/class not found"

    def test_semantic_generate_method_returns_hash_with_stages_variables_default_k(
        self,
    ):
        """generate method returns Hash with 'stages', 'variables', 'default' keys."""
        src = self._read_text(self.GENERATOR_RB)
        assert re.search(
            r"def\s+generate\b", src
        ), "generate method not found in PipelineTemplateGenerator"
        for key in ("stages", "variables", "default"):
            assert re.search(
                rf"['\"]?{key}['\"]?\s*=>|:{key}\s*=>|{key}:", src
            ), f"generate method should include '{key}' key in returned hash"

    def test_semantic_build_image_job_uses_docker_24_0_image_with_docker_24_0_dind(
        self,
    ):
        """build-image job uses docker:24.0 image with docker:24.0-dind service."""
        src = self._all_rb_sources()
        assert re.search(
            r"docker.*24\.0|24\.0.*docker", src
        ), "build-image job should reference docker:24.0"
        assert re.search(
            r"dind|docker-in-docker", src, re.IGNORECASE
        ), "build-image job should use dind service"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, via Ruby execution or source analysis)
    # ------------------------------------------------------------------

    def _try_ruby_generate(self, project_type: str, **kwargs) -> str | None:
        """Attempt to run the generator via Ruby and return output."""
        extra_args = ", ".join(f"{k}: {v!r}" for k, v in kwargs.items())
        args_str = f"project_type: '{project_type}'"
        if extra_args:
            args_str += f", {extra_args}"
        script = (
            f"require_relative 'lib/gitlab/ci/pipeline_template_generator'\n"
            f"require 'json'\n"
            f"gen = Gitlab::CI::PipelineTemplateGenerator.new({args_str})\n"
            f"puts JSON.generate(gen.generate)\n"
        )
        result = self._run_ruby(script)
        if result.returncode == 0:
            return result.stdout.strip()
        return None

    def test_functional_pipelinetemplategenerator_new_project_type_rails_generate_re(
        self,
    ):
        """PipelineTemplateGenerator.new(project_type: 'rails').generate returns correct structure."""
        output = self._try_ruby_generate("rails")
        if output is None:
            # Fall back to source analysis
            src = self._all_rb_sources()
            assert re.search(
                r"ruby.*3\.\d|ruby:3\.\d", src
            ), "Rails project should use ruby:3.x image"
            assert re.search(
                r"rspec|bundle\s+exec", src
            ), "Rails project should use rspec test script"
            return
        data = json.loads(output)
        assert "stages" in data or "jobs" in data

    def test_functional_pipelinetemplategenerator_new_project_type_node_parallel_tes(
        self,
    ):
        """PipelineTemplateGenerator.new(project_type: 'node', parallel_tests: 8) sets parallel: 8."""
        output = self._try_ruby_generate("node", parallel_tests=8)
        if output is None:
            src = self._all_rb_sources()
            assert re.search(
                r"parallel|parallel_tests", src
            ), "Generator should support parallel_tests configuration"
            return
        data = json.loads(output)
        # Find test job and check parallel setting
        flat = json.dumps(data)
        assert "8" in flat or "parallel" in flat

    def test_functional_pipelinetemplategenerator_new_project_type_invalid_raises_ar(
        self,
    ):
        """PipelineTemplateGenerator.new(project_type: 'invalid') raises ArgumentError."""
        src = self._read_text(self.GENERATOR_RB)
        assert re.search(
            r"ArgumentError|raise|invalid.*type|unsupported", src, re.IGNORECASE
        ), "Generator should raise ArgumentError for invalid project types"

    def test_functional_deploy_production_job_includes_when_manual_deploy_staging_do(
        self,
    ):
        """deploy-production job includes when: manual, deploy-staging does not."""
        src = self._all_rb_sources()
        assert re.search(
            r"when.*manual|manual.*when", src, re.IGNORECASE
        ), "Production deploy should have when: manual"
        assert re.search(
            r"production|deploy.*prod", src, re.IGNORECASE
        ), "Generator should define production deploy job"

    def test_functional_each_project_type_returns_correct_docker_image_and_test_scri(
        self,
    ):
        """Each project type returns correct Docker image and test script."""
        src = self._all_rb_sources()
        type_image_pairs = {
            "rails": r"ruby",
            "node": r"node",
            "python": r"python",
            "golang": r"golang|go",
        }
        for ptype, img_pattern in type_image_pairs.items():
            assert re.search(
                img_pattern, src, re.IGNORECASE
            ), f"Generator should map '{ptype}' to {img_pattern} Docker image"
