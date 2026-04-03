"""
Test for 'nx-workspace-patterns' skill — Nx Workspace Patterns
Validates nx.json configuration including targetDefaults, caching, affected settings,
and project.json files with tags, targets, and naming conventions.
"""

import os
import re
import json
import glob
import pytest


class TestNxWorkspacePatterns:
    """Tests for Nx workspace patterns in the nx repo."""

    REPO_DIR = "/workspace/nx"

    def _read(self, relpath):
        full = os.path.join(self.REPO_DIR, relpath)
        with open(full, "r", errors="ignore") as f:
            return f.read()

    def _load_nx_cfg(self):
        content = self._read("nx.json")
        return json.loads(content)

    def _get_project_jsons(self):
        pattern = os.path.join(self.REPO_DIR, "**", "project.json")
        return glob.glob(pattern, recursive=True)

    # --- File Path Checks ---

    def test_nx_json_exists(self):
        """Verifies that nx.json exists."""
        path = os.path.join(self.REPO_DIR, "nx.json")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_project_json_exists(self):
        """Verifies that at least one project.json exists."""
        matches = self._get_project_jsons()
        assert len(matches) > 0, "No project.json files found"

    # --- Semantic Checks ---

    def test_sem_nx_json_parseable(self):
        """nx.json is valid JSON and parseable."""
        nx_cfg = self._load_nx_cfg()
        assert isinstance(nx_cfg, dict), "nx.json does not parse to a dict"

    def test_sem_has_target_defaults_or_runner(self):
        """nx.json has 'targetDefaults' or 'tasksRunnerOptions'."""
        nx_cfg = self._load_nx_cfg()
        assert (
            "targetDefaults" in nx_cfg or "tasksRunnerOptions" in nx_cfg
        ), "Neither targetDefaults nor tasksRunnerOptions found in nx.json"

    def test_sem_at_least_2_project_jsons(self):
        """At least 2 project.json files exist in the workspace."""
        project_jsons = self._get_project_jsons()
        assert (
            len(project_jsons) >= 2
        ), f"Expected >= 2 project.json files, found {len(project_jsons)}"

    # --- Functional Checks ---

    def test_func_build_depends_on(self):
        """Build targetDefault has '^build' in dependsOn."""
        nx_cfg = self._load_nx_cfg()
        build_target = nx_cfg.get("targetDefaults", {}).get("build", {})
        assert "^build" in str(
            build_target.get("dependsOn", [])
        ), "'^build' not found in build dependsOn"

    def test_func_test_cacheable(self):
        """'test' is in cacheable operations or has cache=True in targetDefaults."""
        nx_cfg = self._load_nx_cfg()
        cacheable_ops = (
            nx_cfg.get("tasksRunnerOptions", {})
            .get("default", {})
            .get("options", {})
            .get("cacheableOperations", [])
        )
        test_cache = nx_cfg.get("targetDefaults", {}).get("test", {}).get("cache")
        assert "test" in cacheable_ops or test_cache is True, "test is not cacheable"

    def test_func_lint_cacheable(self):
        """'lint' is in cacheable operations or has cache=True in targetDefaults."""
        nx_cfg = self._load_nx_cfg()
        cacheable_ops = (
            nx_cfg.get("tasksRunnerOptions", {})
            .get("default", {})
            .get("options", {})
            .get("cacheableOperations", [])
        )
        lint_cache = nx_cfg.get("targetDefaults", {}).get("lint", {}).get("cache")
        assert "lint" in cacheable_ops or lint_cache is True, "lint is not cacheable"

    def test_func_affected_default_base(self):
        """affected.defaultBase is 'main', 'master', or 'HEAD~1'."""
        nx_cfg = self._load_nx_cfg()
        affected_cfg = nx_cfg.get("affected", {})
        default_base = affected_cfg.get("defaultBase") or nx_cfg.get("defaultBase")
        assert default_base in (
            "main",
            "master",
            "HEAD~1",
        ), f"affected.defaultBase is '{default_base}', expected main/master/HEAD~1"

    def test_func_projects_parseable(self):
        """All project.json files are valid JSON."""
        project_jsons = self._get_project_jsons()
        assert len(project_jsons) >= 2
        for f in project_jsons:
            with open(f, "r") as fh:
                proj = json.loads(fh.read())
                assert isinstance(proj, dict), f"project.json at {f} is not a dict"

    def test_func_all_projects_have_names(self):
        """All project.json files have a 'name' field."""
        project_jsons = self._get_project_jsons()
        for f in project_jsons:
            with open(f, "r") as fh:
                proj = json.loads(fh.read())
                assert proj.get("name"), f"project.json at {f} has no 'name'"

    def test_func_all_tags_follow_convention(self):
        """All project tags follow 'scope:', 'type:', 'platform:', or 'team:' convention."""
        project_jsons = self._get_project_jsons()
        projects = []
        for f in project_jsons:
            with open(f, "r") as fh:
                projects.append(json.loads(fh.read()))
        all_tags = [tag for p in projects for tag in p.get("tags", [])]
        for t in all_tags:
            assert re.match(
                r"^(scope|type|platform|team):", t
            ), f"Tag '{t}' doesn't follow naming convention (scope:|type:|platform:|team:)"

    def test_func_all_projects_have_targets(self):
        """All project.json files have 'targets' field."""
        project_jsons = self._get_project_jsons()
        for f in project_jsons:
            with open(f, "r") as fh:
                proj = json.loads(fh.read())
                assert "targets" in proj, f"project.json at {f} has no 'targets'"

    def test_func_edge_workspace_root(self):
        """nx.json root config exists and is a valid workspace configuration."""
        nx_cfg = self._load_nx_cfg()
        assert isinstance(nx_cfg, dict)
        # Root should have some configuration
        has_config = any(
            key in nx_cfg
            for key in [
                "targetDefaults",
                "tasksRunnerOptions",
                "affected",
                "defaultBase",
                "plugins",
            ]
        )
        assert has_config, "nx.json appears to have no workspace configuration"

    def test_func_failure_target_defaults_present(self):
        """targetDefaults must be present in nx.json (failure if missing)."""
        nx_cfg = self._load_nx_cfg()
        assert (
            "targetDefaults" in nx_cfg or "tasksRunnerOptions" in nx_cfg
        ), "Missing targetDefaults in nx.json"
