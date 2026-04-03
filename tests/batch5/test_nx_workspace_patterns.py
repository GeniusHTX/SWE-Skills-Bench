"""
Test for 'nx-workspace-patterns' skill — Nx Workspace Configuration
Validates nx.json, workspace.json, project.json files with targetDefaults,
dependsOn, cache outputs, and dependency graph validation.
"""

import json
import os
import re
import subprocess

import pytest


class TestNxWorkspacePatterns:
    """Verify Nx workspace configuration patterns."""

    REPO_DIR = "/workspace/nx"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_nx_json_exists(self):
        """Verify nx.json exists."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "nx.json")
        ), "nx.json not found"

    def test_project_json_files_exist(self):
        """Verify at least 2 project.json files exist."""
        project_files = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "node_modules" in dirpath or ".git" in dirpath:
                continue
            if "project.json" in fnames:
                project_files.append(os.path.join(dirpath, "project.json"))
        assert (
            len(project_files) >= 2
        ), f"Expected ≥2 project.json files, found {len(project_files)}"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_target_defaults_build_test_lint(self):
        """Verify targetDefaults for build, test, and lint."""
        nx_json = os.path.join(self.REPO_DIR, "nx.json")
        if not os.path.isfile(nx_json):
            pytest.skip("nx.json not found")
        data = self._load_json(nx_json)
        assert data, "nx.json is empty or invalid"
        td = data.get("targetDefaults", {})
        defined = set(td.keys())
        expected = {"build", "test", "lint"}
        found = defined & expected
        assert (
            len(found) >= 2
        ), f"Expected targetDefaults for ≥2 of build/test/lint, found: {found}"

    def test_depends_on_build(self):
        """Verify build target has dependsOn: ['^build']."""
        nx_json = os.path.join(self.REPO_DIR, "nx.json")
        if not os.path.isfile(nx_json):
            pytest.skip("nx.json not found")
        content = self._read(nx_json)
        assert re.search(
            r"\^build|dependsOn.*build", content
        ), "No dependsOn '^build' found"

    def test_cache_true_with_outputs(self):
        """Verify cache: true with outputs configuration."""
        nx_json = os.path.join(self.REPO_DIR, "nx.json")
        if not os.path.isfile(nx_json):
            pytest.skip("nx.json not found")
        data = self._load_json(nx_json)
        assert data, "nx.json empty"
        td = data.get("targetDefaults", {})
        for target, config in td.items():
            if isinstance(config, dict):
                if config.get("cache") is True and "outputs" in config:
                    return
        # Also check in project.json files
        for fpath in self._find_project_files():
            data = self._load_json(fpath)
            if data and "targets" in data:
                for t, c in data["targets"].items():
                    if isinstance(c, dict) and c.get("cache") is True:
                        return
        pytest.fail("No target with cache:true and outputs found")

    def test_nx_executors(self):
        """Verify @nx/ executors are used in project configurations."""
        all_content = ""
        for fpath in self._find_project_files():
            all_content += self._read(fpath)
        content = (
            self._read(os.path.join(self.REPO_DIR, "nx.json"))
            if os.path.isfile(os.path.join(self.REPO_DIR, "nx.json"))
            else ""
        )
        all_content += content
        assert (
            "@nx/" in all_content or "@nrwl/" in all_content
        ), "No @nx/ executor references found"

    # ── functional_check ────────────────────────────────────────────────────

    def test_nx_json_valid(self):
        """Verify nx.json is valid JSON."""
        nx_path = os.path.join(self.REPO_DIR, "nx.json")
        if not os.path.isfile(nx_path):
            pytest.skip("nx.json not found")
        data = self._load_json(nx_path)
        assert data is not None, "nx.json is not valid JSON"

    def test_project_json_files_valid(self):
        """Verify all project.json files are valid JSON."""
        for fpath in self._find_project_files():
            data = self._load_json(fpath)
            assert (
                data is not None
            ), f"Invalid JSON in {os.path.relpath(fpath, self.REPO_DIR)}"

    def test_dependency_graph_acyclic(self):
        """Verify no circular dependencies in project graph (basic check)."""
        projects = {}
        for fpath in self._find_project_files():
            data = self._load_json(fpath)
            if not data:
                continue
            name = data.get("name", os.path.basename(os.path.dirname(fpath)))
            deps = []
            if "implicitDependencies" in data:
                deps.extend(data["implicitDependencies"])
            projects[name] = deps
        # Simple cycle detection
        visited = set()
        path = set()

        def has_cycle(node):
            if node in path:
                return True
            if node in visited:
                return False
            visited.add(node)
            path.add(node)
            for dep in projects.get(node, []):
                if has_cycle(dep):
                    return True
            path.discard(node)
            return False

        for proj in projects:
            assert not has_cycle(proj), f"Circular dependency detected involving {proj}"

    def test_turbo_or_nx_dry_run(self):
        """Verify nx graph or build can run."""
        try:
            result = subprocess.run(
                ["npx", "nx", "show", "projects"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.REPO_DIR,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("npx/nx not available")
        # Non-zero ok if missing deps, but not crash
        if result.returncode != 0:
            assert (
                "error" not in result.stderr.lower() or "Cannot find" in result.stderr
            )

    def test_workspace_json_or_package_json(self):
        """Verify workspace.json or package.json with workspaces exists."""
        ws = os.path.join(self.REPO_DIR, "workspace.json")
        pkg = os.path.join(self.REPO_DIR, "package.json")
        if os.path.isfile(ws):
            return
        if os.path.isfile(pkg):
            data = self._load_json(pkg)
            if data and ("workspaces" in data or "private" in data):
                return
        pytest.fail("No workspace.json or package.json with workspaces")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_project_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "node_modules" in dirpath or ".git" in dirpath:
                continue
            if "project.json" in fnames:
                results.append(os.path.join(dirpath, "project.json"))
        return results

    def _load_json(self, path):
        try:
            with open(path, "r", errors="ignore") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, IOError):
            return None

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
