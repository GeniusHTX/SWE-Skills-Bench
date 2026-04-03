"""
Test for 'turborepo' skill — Turborepo Monorepo Configuration
Validates that the Agent created proper turbo.json pipeline configuration
with build/dev/test tasks, workspace setup, and caching strategy.
"""

import glob
import json
import os

import pytest


class TestTurborepo:
    """Verify Turborepo monorepo configuration."""

    REPO_DIR = "/workspace/turbo"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _load_turbo_cfg(self):
        return json.loads(open(os.path.join(self.REPO_DIR, "turbo.json")).read())

    def _load_pipeline(self):
        cfg = self._load_turbo_cfg()
        return cfg.get("pipeline") or cfg.get("tasks")

    # ---- file_path_check ----

    def test_turbo_json_exists(self):
        """Verifies turbo.json exists."""
        path = os.path.join(self.REPO_DIR, "turbo.json")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_package_json_exists(self):
        """Verifies package.json exists."""
        path = os.path.join(self.REPO_DIR, "package.json")
        assert os.path.exists(path), f"Expected file not found: {path}"

    # ---- semantic_check ----

    def test_sem_turbo_json_parseable(self):
        """Verifies turbo.json is valid JSON."""
        turbo_cfg = self._load_turbo_cfg()
        assert isinstance(turbo_cfg, dict), "turbo.json is not a valid JSON object"

    def test_sem_pipeline_exists(self):
        """Verifies pipeline (or tasks) key exists."""
        pipeline = self._load_pipeline()
        assert pipeline is not None, "pipeline/tasks key missing from turbo.json"

    def test_sem_build_in_pipeline(self):
        """Verifies 'build' task is defined in pipeline."""
        pipeline = self._load_pipeline()
        assert "build" in pipeline, "'build' not found in pipeline"

    def test_sem_workspaces_in_package_json(self):
        """Verifies workspaces defined in package.json (edge case)."""
        root_pkg = json.loads(open(os.path.join(self.REPO_DIR, "package.json")).read())
        assert "workspaces" in root_pkg, "'workspaces' missing from package.json"

    # ---- functional_check ----

    def test_func_build_depends_on(self):
        """Verifies build task has ^build in dependsOn."""
        pipeline = self._load_pipeline()
        build_cfg = pipeline["build"]
        assert "^build" in build_cfg.get(
            "dependsOn", []
        ), "'^build' not in build dependsOn"

    def test_func_build_outputs(self):
        """Verifies build task has outputs defined (edge case)."""
        pipeline = self._load_pipeline()
        build_cfg = pipeline["build"]
        assert build_cfg.get("outputs") is not None, "build outputs is None"
        assert len(build_cfg["outputs"]) >= 1, "build outputs is empty"

    def test_func_dev_cache_disabled(self):
        """Verifies dev task has cache=false or persistent=true."""
        pipeline = self._load_pipeline()
        dev_cfg = pipeline.get("dev", {})
        assert (
            dev_cfg.get("cache") is False or dev_cfg.get("persistent") is True
        ), "dev task should have cache=false or persistent=true"

    def test_func_test_depends_on_build(self):
        """Verifies test task depends on build."""
        pipeline = self._load_pipeline()
        test_cfg = pipeline.get("test", {})
        assert (
            "build" in test_cfg.get("dependsOn", []) or "dependsOn" not in test_cfg
        ), "test task should depend on build or use implicit"

    def test_func_workspaces_structure(self):
        """Verifies workspaces list contains packages/ or apps/ patterns."""
        root_pkg = json.loads(open(os.path.join(self.REPO_DIR, "package.json")).read())
        workspaces = root_pkg["workspaces"]
        assert isinstance(workspaces, list), "workspaces is not a list"
        assert any(
            "packages/" in w or "apps/" in w for w in workspaces
        ), "No packages/ or apps/ pattern in workspaces"

    def test_func_workspace_packages_exist(self):
        """Verifies at least one workspace package.json exists."""
        pkg_jsons = glob.glob(
            os.path.join(self.REPO_DIR, "packages/*/package.json")
        ) + glob.glob(os.path.join(self.REPO_DIR, "apps/*/package.json"))
        assert len(pkg_jsons) >= 1, "No workspace package.json files found"

    def test_func_all_packages_have_name(self):
        """Verifies all workspace packages have a name field."""
        pkg_jsons = glob.glob(
            os.path.join(self.REPO_DIR, "packages/*/package.json")
        ) + glob.glob(os.path.join(self.REPO_DIR, "apps/*/package.json"))
        assert all(
            json.loads(open(f).read()).get("name") for f in pkg_jsons
        ), "Some workspace packages missing 'name' field"

    def test_func_global_dependencies(self):
        """Verifies globalDependencies or globalEnv configured (edge case)."""
        turbo_cfg = self._load_turbo_cfg()
        assert (
            turbo_cfg.get("globalDependencies")
            or turbo_cfg.get("globalEnv") is not None
            or ".env" in str(turbo_cfg)
        ), "globalDependencies/globalEnv not configured"

    def test_func_failure_build_missing_depends_on(self):
        """Failure case: build task should have ^build in dependsOn."""
        pipeline = self._load_pipeline()
        build_cfg = pipeline["build"]
        depends_on = build_cfg.get("dependsOn", [])
        assert "^build" in depends_on, f"build dependsOn={depends_on} missing '^build'"
