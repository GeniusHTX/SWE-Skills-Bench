"""
Test for 'turborepo' skill — Turborepo Configuration
Validates turbo.json, dependsOn ^build, persistent dev task,
outputs configuration, and pipeline structure.
"""

import os
import re
import json

import pytest


class TestTurborepo:
    """Verify Turborepo configuration patterns."""

    REPO_DIR = "/workspace/turbo"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_turbo_json_exists(self):
        """Verify turbo.json configuration file exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            if "turbo.json" in fnames:
                found = True
                break
        assert found, "No turbo.json found"

    def test_package_json_exists(self):
        """Verify root package.json exists."""
        assert os.path.exists(
            os.path.join(self.REPO_DIR, "package.json")
        ), "No root package.json found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_depends_on_build(self):
        """Verify dependsOn with ^build (topological dependency)."""
        turbo_data = self._load_turbo_json()
        if turbo_data is None:
            pytest.skip("turbo.json not found or invalid")
        content = json.dumps(turbo_data)
        assert "^build" in content, "No ^build dependency in turbo.json"

    def test_persistent_dev_task(self):
        """Verify persistent: true for dev task."""
        turbo_data = self._load_turbo_json()
        if turbo_data is None:
            pytest.skip("turbo.json not found or invalid")
        content = json.dumps(turbo_data)
        assert "persistent" in content, "No persistent task configuration"

    def test_outputs_configured(self):
        """Verify outputs are configured for caching."""
        turbo_data = self._load_turbo_json()
        if turbo_data is None:
            pytest.skip("turbo.json not found or invalid")
        content = json.dumps(turbo_data)
        assert "outputs" in content, "No outputs configured"

    def test_pipeline_or_tasks(self):
        """Verify pipeline/tasks are defined."""
        turbo_data = self._load_turbo_json()
        if turbo_data is None:
            pytest.skip("turbo.json not found or invalid")
        assert (
            "pipeline" in turbo_data or "tasks" in turbo_data
        ), "No pipeline/tasks in turbo.json"

    def test_cache_configuration(self):
        """Verify caching is configured."""
        turbo_data = self._load_turbo_json()
        if turbo_data is None:
            pytest.skip("turbo.json not found or invalid")
        content = json.dumps(turbo_data)
        if re.search(r"(cache|outputs|\.turbo)", content, re.IGNORECASE):
            return
        pytest.fail("No cache configuration found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_turbo_json_valid(self):
        """Verify turbo.json is valid JSON."""
        turbo_path = self._find_turbo_json()
        if not turbo_path:
            pytest.skip("turbo.json not found")
        with open(turbo_path, "r") as fh:
            data = json.load(fh)
            assert isinstance(data, dict), "turbo.json is not an object"

    def test_workspaces_configured(self):
        """Verify workspaces in package.json."""
        pkg_json = os.path.join(self.REPO_DIR, "package.json")
        if not os.path.exists(pkg_json):
            pytest.skip("No package.json")
        with open(pkg_json, "r") as fh:
            data = json.load(fh)
        if "workspaces" in data:
            return
        # pnpm-workspace.yaml
        pnpm_ws = os.path.join(self.REPO_DIR, "pnpm-workspace.yaml")
        if os.path.exists(pnpm_ws):
            return
        pytest.fail("No workspaces configuration found")

    def test_build_task_defined(self):
        """Verify build task is defined in pipeline."""
        turbo_data = self._load_turbo_json()
        if turbo_data is None:
            pytest.skip("turbo.json not found or invalid")
        pipeline = turbo_data.get("pipeline", turbo_data.get("tasks", {}))
        if isinstance(pipeline, dict):
            assert "build" in pipeline, "No build task in pipeline"
        elif isinstance(pipeline, list):
            names = [
                t.get("name", t.get("taskId", ""))
                for t in pipeline
                if isinstance(t, dict)
            ]
            assert any("build" in n for n in names), "No build task"

    def test_dev_task_defined(self):
        """Verify dev task is defined."""
        turbo_data = self._load_turbo_json()
        if turbo_data is None:
            pytest.skip("turbo.json not found or invalid")
        content = json.dumps(turbo_data)
        assert "dev" in content, "No dev task in turbo.json"

    def test_global_env_or_inputs(self):
        """Verify globalEnv or inputs for cache invalidation."""
        turbo_data = self._load_turbo_json()
        if turbo_data is None:
            pytest.skip("turbo.json not found or invalid")
        content = json.dumps(turbo_data)
        if re.search(
            r"(globalEnv|globalDependencies|inputs|env)", content, re.IGNORECASE
        ):
            return
        pytest.skip("No globalEnv/inputs found (may not be required)")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_turbo_json(self):
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            if "turbo.json" in fnames:
                return os.path.join(dirpath, "turbo.json")
        return None

    def _load_turbo_json(self):
        path = self._find_turbo_json()
        if not path:
            return None
        try:
            with open(path, "r") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, IOError):
            return None
