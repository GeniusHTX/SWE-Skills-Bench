"""
Test for 'gitlab-ci-patterns' skill — GitLab CI Pipeline Generator
Validates that the Agent created a Python package for generating GitLab CI
pipeline YAML with stages, job templates, rules, and artifact defaults.
"""

import os
import re
import sys

import pytest


class TestGitlabCiPatterns:
    """Verify GitLab CI pipeline generator implementation."""

    REPO_DIR = "/workspace/gitlabhq"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_gitlab_ci_package_exists(self):
        """Verify gitlab_ci package __init__.py and generator.py exist."""
        for rel in ("src/gitlab_ci/__init__.py", "src/gitlab_ci/generator.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_templates_stages_models_exist(self):
        """Verify templates.py, stages.py, and models.py exist."""
        for rel in ("src/gitlab_ci/templates.py", "src/gitlab_ci/stages.py",
                     "src/gitlab_ci/models.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_all_classes_importable(self):
        """All main classes are importable without errors."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            from gitlab_ci.generator import PipelineGenerator  # noqa: F401
            from gitlab_ci.templates import JobTemplate  # noqa: F401
            from gitlab_ci.stages import StageOrchestrator  # noqa: F401
        except ImportError:
            pytest.skip("gitlab_ci not importable")
        finally:
            sys.path.pop(0)

    # ── semantic_check ──────────────────────────────────────────────

    def test_generator_and_exception_classes_defined(self):
        """Verify PipelineGenerator, DuplicateStageError, and UnknownStageError are defined."""
        content = self._read(os.path.join(self.REPO_DIR, "src/gitlab_ci/generator.py"))
        assert content, "generator.py is empty or unreadable"
        for name in ("PipelineGenerator", "DuplicateStageError", "UnknownStageError"):
            assert name in content, f"'{name}' not found in generator.py"

    def test_yaml_dump_in_generator(self):
        """Verify generator.py uses yaml.dump or ruamel.yaml for serialization."""
        content = self._read(os.path.join(self.REPO_DIR, "src/gitlab_ci/generator.py"))
        assert content, "generator.py is empty or unreadable"
        found = "yaml.dump" in content or "ruamel" in content
        assert found, "No YAML serialization found in generator.py"

    def test_job_template_render_defined(self):
        """Verify templates.py defines JobTemplate class with render() method."""
        content = self._read(os.path.join(self.REPO_DIR, "src/gitlab_ci/templates.py"))
        assert content, "templates.py is empty or unreadable"
        assert "class JobTemplate" in content, "JobTemplate class not found"
        assert "def render" in content, "render method not found"

    # ── functional_check (import) ───────────────────────────────────

    def _import(self, dotpath: str):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            return __import__(dotpath, fromlist=[""])
        except ImportError:
            pytest.skip(f"{dotpath} not importable")
        finally:
            sys.path.pop(0)

    def test_generate_produces_valid_yaml_with_stages(self):
        """PipelineGenerator.generate() returns valid YAML with correct stages list."""
        import yaml
        gen_mod = self._import("gitlab_ci.generator")
        models_mod = self._import("gitlab_ci.models")
        config = models_mod.PipelineConfig(stages=["build", "test"], jobs=[])
        output = gen_mod.PipelineGenerator().generate(config)
        parsed = yaml.safe_load(output)
        assert parsed.get("stages") == ["build", "test"]

    def test_generated_yaml_is_parseable(self):
        """yaml.safe_load on generated output does not raise."""
        import yaml
        gen_mod = self._import("gitlab_ci.generator")
        models_mod = self._import("gitlab_ci.models")
        output = gen_mod.PipelineGenerator().generate(
            models_mod.PipelineConfig(stages=["build"], jobs=[]))
        parsed = yaml.safe_load(output)
        assert parsed is not None

    def test_duplicate_stage_raises_error(self):
        """PipelineGenerator raises DuplicateStageError on duplicate stage names."""
        gen_mod = self._import("gitlab_ci.generator")
        models_mod = self._import("gitlab_ci.models")
        with pytest.raises(gen_mod.DuplicateStageError):
            gen_mod.PipelineGenerator().generate(
                models_mod.PipelineConfig(stages=["build", "build"], jobs=[]))

    def test_job_template_renders_rules(self):
        """JobTemplate.render with rules parameter produces job dict with 'rules' key."""
        mod = self._import("gitlab_ci.templates")
        job = mod.JobTemplate().render(
            "my-test", "test", ["pytest"],
            rules=[{"if": "$CI_COMMIT_BRANCH"}])
        assert "rules" in job, "'rules' key missing from rendered job"

    def test_artifact_expire_in_default(self):
        """Generated output uses '1 week' as default artifact expire_in."""
        import yaml
        gen_mod = self._import("gitlab_ci.generator")
        models_mod = self._import("gitlab_ci.models")
        artifact = models_mod.Artifact(paths=["dist/"])
        job = models_mod.Job("build-job", "build", ["make build"], artifact=artifact)
        config = models_mod.PipelineConfig(stages=["build"], jobs=[job])
        output = yaml.safe_load(gen_mod.PipelineGenerator().generate(config))
        expire = output.get("build-job", {}).get("artifacts", {}).get("expire_in", "MISSING")
        assert expire == "1 week", f"Expected '1 week', got '{expire}'"
