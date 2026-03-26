"""
Test for 'nx-workspace-patterns' skill — Nx Monorepo Workspace Patterns
Validates that the Agent configured Nx workspace with generators, plugins,
and proper dependency graph setup.
"""

import os
import json
import subprocess
import pytest


class TestNxWorkspacePatterns:
    """Verify Nx workspace configuration and generators."""

    REPO_DIR = "/workspace/nx"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_workspace_config_exists(self):
        """nx.json or workspace.json must exist."""
        paths = [
            os.path.join(self.REPO_DIR, "nx.json"),
            os.path.join(self.REPO_DIR, "workspace.json"),
        ]
        found = any(os.path.isfile(p) for p in paths)
        if not found:
            for root, dirs, files in os.walk(self.REPO_DIR):
                if "nx.json" in files and "node_modules" not in root:
                    found = True
                    break
        assert found, "nx.json not found"

    def test_generator_exists(self):
        """Custom generator/schematic must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if (
                    ("generator" in f.lower() or "schematic" in f.lower())
                    and f.endswith((".ts", ".js"))
                    and "node_modules" not in root
                ):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No generator/schematic file found"

    def test_generator_schema_exists(self):
        """Generator must have a schema.json."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if (
                "schema.json" in files
                and "node_modules" not in root
                and ("generator" in root.lower() or "schematic" in root.lower())
            ):
                found = True
                break
        if not found:
            # Broader search
            for root, dirs, files in os.walk(self.REPO_DIR):
                if "schema.json" in files and "node_modules" not in root:
                    fpath = os.path.join(root, "schema.json")
                    with open(fpath, "r", errors="ignore") as f:
                        content = f.read()
                    if "properties" in content:
                        found = True
                        break
        assert found, "No generator schema.json found"

    # ------------------------------------------------------------------
    # L2: configuration & content validation
    # ------------------------------------------------------------------

    def _find_nx_json(self):
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "nx.json" in files and "node_modules" not in root:
                return os.path.join(root, "nx.json")
        return None

    def test_nx_json_valid(self):
        """nx.json must be valid JSON."""
        fpath = self._find_nx_json()
        assert fpath, "nx.json not found"
        with open(fpath, "r") as f:
            config = json.load(f)
        assert isinstance(config, dict)

    def test_nx_has_targets_or_plugins(self):
        """nx.json must configure targets/plugins/generators."""
        fpath = self._find_nx_json()
        assert fpath, "nx.json not found"
        with open(fpath, "r") as f:
            config = json.load(f)
        keys = set(config.keys())
        expected_keys = {
            "targetDefaults",
            "plugins",
            "generators",
            "defaultProject",
            "tasksRunnerOptions",
            "namedInputs",
            "targets",
        }
        found = keys & expected_keys
        assert len(found) >= 1, f"nx.json missing expected config; keys: {keys}"

    def test_generator_has_tree_param(self):
        """Generator function must accept Tree parameter."""
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if (
                    ("generator" in f.lower() or "schematic" in f.lower())
                    and f.endswith((".ts", ".js"))
                    and "node_modules" not in root
                ):
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", errors="ignore") as fh:
                        content = fh.read()
                    tree_patterns = ["Tree", "tree", "host", "SchematicContext"]
                    if any(p in content for p in tree_patterns):
                        return
        pytest.fail("No generator with Tree parameter found")

    def test_generator_creates_files(self):
        """Generator must create or modify files."""
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if (
                    ("generator" in f.lower() or "schematic" in f.lower())
                    and f.endswith((".ts", ".js"))
                    and "node_modules" not in root
                ):
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", errors="ignore") as fh:
                        content = fh.read()
                    file_ops = [
                        "generateFiles",
                        "addProjectConfiguration",
                        "tree.write",
                        "tree.create",
                        "apply",
                        "template",
                        "mergeWith",
                    ]
                    if any(p in content for p in file_ops):
                        return
        pytest.fail("Generator doesn't appear to create/modify files")

    def test_schema_has_properties(self):
        """schema.json must define input properties."""
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "schema.json" in files and "node_modules" not in root:
                fpath = os.path.join(root, "schema.json")
                with open(fpath, "r", errors="ignore") as f:
                    schema = json.load(f)
                if "properties" in schema:
                    props = schema["properties"]
                    assert len(props) >= 1, "schema.json has no properties"
                    return
        pytest.fail("No schema.json with properties found")

    def test_generator_has_tests(self):
        """Generator test file must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if (
                    "generator" in f.lower()
                    and ("spec" in f.lower() or "test" in f.lower())
                    and f.endswith((".ts", ".js"))
                    and "node_modules" not in root
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No generator test file found"

    def test_project_json_or_config(self):
        """At least one project.json or project configuration must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "project.json" in files and "node_modules" not in root:
                found = True
                break
        assert found, "No project.json found"
