"""
Test for 'nx-workspace-patterns' skill — Nx monorepo workspace patterns
Validates that the Agent created Nx workspace configuration, project structure,
and build/test targets in the nx project.
"""

import os
import re

import pytest


class TestNxWorkspacePatterns:
    """Verify Nx workspace configuration patterns."""

    REPO_DIR = "/workspace/nx"

    def test_nx_json_exists(self):
        """nx.json must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "nx.json" in files:
                found = True
                break
        assert found, "nx.json not found"

    def test_workspace_json_or_project_json(self):
        """workspace.json or at least one project.json must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("workspace.json", "project.json"):
                    found = True
                    break
            if found:
                break
        assert found, "No workspace.json or project.json found"

    def test_package_json_exists(self):
        """Root package.json must exist."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, "package.json")), \
            "Root package.json not found"

    def test_apps_or_packages_directory(self):
        """apps/ or packages/ directory must exist."""
        found = False
        for d in ("apps", "packages", "libs"):
            if os.path.isdir(os.path.join(self.REPO_DIR, d)):
                found = True
                break
        assert found, "No apps/, packages/, or libs/ directory found"

    def test_build_target_configured(self):
        """At least one project must have a build target."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "project.json":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"\"build\"", content):
                        found = True
                        break
            if found:
                break
        assert found, "No build target configured"

    def test_test_target_configured(self):
        """At least one project must have a test target."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "project.json":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"\"test\"", content):
                        found = True
                        break
            if found:
                break
        assert found, "No test target configured"

    def test_tsconfig_base_exists(self):
        """tsconfig.base.json or tsconfig.json must exist."""
        found = False
        for f in ("tsconfig.base.json", "tsconfig.json"):
            if os.path.isfile(os.path.join(self.REPO_DIR, f)):
                found = True
                break
        assert found, "No tsconfig found"

    def test_nx_affected_or_cache_config(self):
        """nx.json should configure affected or cache settings."""
        nx_path = None
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "nx.json" in files:
                nx_path = os.path.join(root, "nx.json")
                break
        assert nx_path is not None
        with open(nx_path, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"affected|cacheableOperations|targetDefaults|namedInputs|tasksRunnerOptions", content), \
            "nx.json does not configure affected or cache"

    def test_dependency_graph_or_implicit(self):
        """Projects should define dependencies or implicit dependencies."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("project.json", "nx.json"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"implicitDependencies|dependsOn|dependencies", content):
                        found = True
                        break
            if found:
                break
        assert found, "No dependency configuration found"

    def test_generator_or_executor(self):
        """Custom generator or executor should exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".ts", ".js", ".json")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"generator|executor|@nrwl|@nx/|createNodes|createDependencies", content):
                        found = True
                        break
            if found:
                break
        assert found, "No generator or executor found"
