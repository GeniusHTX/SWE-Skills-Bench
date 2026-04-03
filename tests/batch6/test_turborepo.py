"""
Tests for 'turborepo' skill — Turborepo Monorepo Build System.
Validates that the Agent configured a Turborepo monorepo with correct
turbo.json pipeline, proper dependency ordering (^build), caching policies,
workspace globs, and JSON validity.
"""

import glob
import json
import os
import re
import subprocess

import pytest


class TestTurborepo:
    """Verify Turborepo monorepo configuration."""

    REPO_DIR = "/workspace/turbo"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _safe_read(path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()

    @staticmethod
    def _load_json(path: str):
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return json.load(fh)

    @classmethod
    def _run_in_repo(cls, cmd: str, timeout: int = 120) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd,
            cwd=cls.REPO_DIR,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    # ── file_path_check (static) ────────────────────────────────────────

    def test_turbo_json_exists(self):
        """Verify turbo.json configuration file exists at the workspace root."""
        path = os.path.join(self.REPO_DIR, "turbo.json")
        assert os.path.isfile(path), f"Missing {path}"

    def test_root_package_json_has_workspaces(self):
        """Verify root package.json exists and contains workspaces field."""
        path = os.path.join(self.REPO_DIR, "package.json")
        assert os.path.isfile(path), f"Missing {path}"
        pkg = self._load_json(path)
        assert "workspaces" in pkg, "root package.json missing 'workspaces' field"

    def test_packages_directory_has_multiple_packages(self):
        """Verify packages/ directory contains at least 2 sub-packages."""
        patterns = [
            os.path.join(self.REPO_DIR, "packages", "*", "package.json"),
            os.path.join(self.REPO_DIR, "apps", "*", "package.json"),
            os.path.join(self.REPO_DIR, "crates", "*", "Cargo.toml"),
        ]
        total = sum(len(glob.glob(p)) for p in patterns)
        assert total >= 2, f"Expected >= 2 sub-packages, found {total}"

    # ── semantic_check (static) ─────────────────────────────────────────

    def test_build_depends_on_caret_build(self):
        """Verify build task uses '^build' in dependsOn for topological ordering."""
        turbo_path = os.path.join(self.REPO_DIR, "turbo.json")
        turbo = self._load_json(turbo_path)
        pipeline = turbo.get("pipeline", turbo.get("tasks", {}))
        build = pipeline.get("build", {})
        deps = build.get("dependsOn", [])
        assert "^build" in deps, f"build.dependsOn should contain '^build', got {deps}"

    def test_dev_cache_false(self):
        """Verify dev task has cache explicitly set to false."""
        turbo_path = os.path.join(self.REPO_DIR, "turbo.json")
        turbo = self._load_json(turbo_path)
        pipeline = turbo.get("pipeline", turbo.get("tasks", {}))
        dev = pipeline.get("dev", {})
        assert (
            dev.get("cache") is False
        ), f"dev.cache should be false, got {dev.get('cache')!r}"

    def test_env_or_global_env_declared(self):
        """Verify globalEnv or per-task env arrays are present for cache busting."""
        turbo_path = os.path.join(self.REPO_DIR, "turbo.json")
        turbo = self._load_json(turbo_path)
        global_env = turbo.get("globalEnv", [])
        pipeline = turbo.get("pipeline", turbo.get("tasks", {}))
        any_task_env = any(
            t.get("env") for t in pipeline.values() if isinstance(t, dict)
        )
        assert (
            global_env or any_task_env
        ), "No globalEnv or per-task env declarations found"

    # ── functional_check ────────────────────────────────────────────────

    def test_turbo_json_valid_json_parse(self):
        """Verify turbo.json is valid JSON parseable without errors."""
        turbo_path = os.path.join(self.REPO_DIR, "turbo.json")
        data = self._load_json(turbo_path)
        assert isinstance(data, dict), "turbo.json root should be an object"

    def test_pipeline_has_build_task(self):
        """Verify turbo.json pipeline/tasks contains a build task definition."""
        turbo_path = os.path.join(self.REPO_DIR, "turbo.json")
        turbo = self._load_json(turbo_path)
        pipeline = turbo.get("pipeline", turbo.get("tasks", {}))
        assert "build" in pipeline, "'build' task not found in pipeline/tasks"

    def test_test_task_has_outputs(self):
        """Verify test task outputs is defined for caching test results."""
        turbo_path = os.path.join(self.REPO_DIR, "turbo.json")
        turbo = self._load_json(turbo_path)
        pipeline = turbo.get("pipeline", turbo.get("tasks", {}))
        test_task = pipeline.get("test", {})
        outputs = test_task.get("outputs", [])
        assert outputs, f"test.outputs should be non-empty, got {outputs!r}"

    def test_workspaces_array_has_glob_patterns(self):
        """Verify root package.json workspaces contain glob patterns."""
        pkg_path = os.path.join(self.REPO_DIR, "package.json")
        pkg = self._load_json(pkg_path)
        workspaces = pkg.get("workspaces", [])
        if isinstance(workspaces, dict):
            workspaces = workspaces.get("packages", [])
        has_glob = any("*" in w for w in workspaces)
        assert has_glob, f"workspaces should contain glob patterns, got {workspaces}"

    def test_turbo_json_syntax_error_detected(self):
        """Verify that a malformed JSON string raises JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            json.loads("{invalid json}")

    def test_build_without_caret_detected(self):
        """Verify detection when build.dependsOn uses 'build' instead of '^build'."""
        turbo_path = os.path.join(self.REPO_DIR, "turbo.json")
        turbo = self._load_json(turbo_path)
        pipeline = turbo.get("pipeline", turbo.get("tasks", {}))
        deps = pipeline.get("build", {}).get("dependsOn", [])
        assert (
            "^build" in deps
        ), "build.dependsOn missing '^build' — packages could build out of order"
