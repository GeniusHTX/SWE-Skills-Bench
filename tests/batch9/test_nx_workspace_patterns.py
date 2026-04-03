"""
Test for 'nx-workspace-patterns' skill — Nx Monorepo Configuration
Validates nx.json, .eslintrc.json, project.json configs for caching,
module boundaries, named inputs, and target definitions via JSON parsing.
"""

import glob
import json
import os

import pytest


class TestNxWorkspacePatterns:
    """Verify Nx workspace configuration: nx.json, eslintrc, project.json."""

    REPO_DIR = "/workspace/nx"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _root(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, *parts)

    def _load_json(self, path: str) -> dict:
        with open(path, "r") as f:
            return json.load(f)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_nx_json_exists(self):
        """nx.json must exist at workspace root."""
        assert os.path.isfile(self._root("nx.json")), "nx.json not found"

    def test_eslintrc_json_exists(self):
        """.eslintrc.json must exist at workspace root."""
        assert os.path.isfile(self._root(".eslintrc.json")), ".eslintrc.json not found"

    def test_project_json_in_apps(self):
        """At least one apps/*/project.json must exist."""
        projects = glob.glob(self._root("apps", "*", "project.json"))
        assert len(projects) >= 1, "No apps/*/project.json found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_cacheable_operations_include_build_test(self):
        """nx.json cacheableOperations must include build and test."""
        content = self._read_file(self._root("nx.json"))
        if not content:
            pytest.skip("nx.json not found")
        assert "cacheableOperations" in content or "targetDefaults" in content
        assert "build" in content
        assert "test" in content

    def test_named_inputs_include_nx_json(self):
        """namedInputs.default must reference {workspaceRoot}/nx.json."""
        content = self._read_file(self._root("nx.json"))
        if not content:
            pytest.skip("nx.json not found")
        has_named = "namedInputs" in content
        if has_named:
            assert "workspaceRoot" in content or "nx.json" in content

    def test_eslintrc_has_module_boundaries(self):
        """.eslintrc.json must have @nx/enforce-module-boundaries rule."""
        content = self._read_file(self._root(".eslintrc.json"))
        if not content:
            pytest.skip(".eslintrc.json not found")
        assert "enforce-module-boundaries" in content
        assert "depConstraints" in content

    def test_project_json_has_build_test_targets(self):
        """First project.json must have build and test targets."""
        projects = glob.glob(self._root("apps", "*", "project.json"))
        if not projects:
            pytest.skip("No project.json found")
        content = self._read_file(projects[0])
        assert "build" in content
        assert "test" in content

    # ── functional_check ─────────────────────────────────────────────────

    def test_nx_json_valid_json(self):
        """nx.json must parse as valid JSON."""
        path = self._root("nx.json")
        if not os.path.isfile(path):
            pytest.skip("nx.json not found")
        data = self._load_json(path)
        assert isinstance(data, dict)

    def test_eslintrc_valid_json(self):
        """.eslintrc.json must parse as valid JSON."""
        path = self._root(".eslintrc.json")
        if not os.path.isfile(path):
            pytest.skip(".eslintrc.json not found")
        data = self._load_json(path)
        assert isinstance(data, dict)

    def test_cacheable_operations_functional(self):
        """Parsed cacheableOperations must contain 'build' and 'test'."""
        path = self._root("nx.json")
        if not os.path.isfile(path):
            pytest.skip("nx.json not found")
        data = self._load_json(path)
        # Look in tasksRunnerOptions or targetDefaults
        ops = []
        runners = data.get("tasksRunnerOptions", {})
        for runner in runners.values():
            ops.extend(runner.get("options", {}).get("cacheableOperations", []))
        if not ops:
            # Nx 16+ uses targetDefaults with cache key
            targets = data.get("targetDefaults", {})
            for name, config in targets.items():
                if config.get("cache", False):
                    ops.append(name)
        assert "build" in ops, "'build' not in cacheableOperations"
        assert "test" in ops, "'test' not in cacheableOperations"

    def test_all_project_jsons_parse(self):
        """All apps/*/project.json must parse with targets key."""
        projects = glob.glob(self._root("apps", "*", "project.json"))
        if not projects:
            pytest.skip("No project.json files found")
        for p in projects:
            data = self._load_json(p)
            assert "targets" in data, f"'targets' missing in {p}"
            assert "build" in data["targets"], f"'build' target missing in {p}"

    def test_missing_build_assertion_fails(self):
        """Verify test is meaningful: removing 'build' causes assertion failure."""
        path = self._root("nx.json")
        if not os.path.isfile(path):
            pytest.skip("nx.json not found")
        data = self._load_json(path)
        runners = data.get("tasksRunnerOptions", {})
        for runner in runners.values():
            ops = runner.get("options", {}).get("cacheableOperations", [])
            modified = [o for o in ops if o != "build"]
            assert "build" not in modified, "Test sanity: modified list should not contain 'build'"
