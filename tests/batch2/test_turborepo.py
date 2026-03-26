"""
Test for 'turborepo' skill — Turborepo Cache Demo
Validates that the Agent created a cache-demo example for Turborepo
with workspaces, pipeline config, shared packages, and build scripts.
"""

import os
import re
import json

import pytest


class TestTurborepo:
    """Verify Turborepo cache-demo example."""

    REPO_DIR = "/workspace/turbo"
    DEMO_DIR = "examples/cache-demo"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: Root config files
    # ------------------------------------------------------------------

    def test_root_package_json_exists(self):
        """Root package.json must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.DEMO_DIR, "package.json")
        )

    def test_turbo_json_exists(self):
        """turbo.json must exist."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, self.DEMO_DIR, "turbo.json"))

    def test_root_package_json_valid(self):
        """Root package.json must be valid JSON."""
        content = self._read(self.DEMO_DIR, "package.json")
        data = json.loads(content)
        assert "name" in data or "private" in data

    def test_turbo_json_valid(self):
        """turbo.json must be valid JSON."""
        content = self._read(self.DEMO_DIR, "turbo.json")
        json.loads(content)

    # ------------------------------------------------------------------
    # L1: Workspaces configuration
    # ------------------------------------------------------------------

    def test_workspaces_configured(self):
        """Root package.json must configure workspaces."""
        content = self._read(self.DEMO_DIR, "package.json")
        data = json.loads(content)
        assert "workspaces" in data, "No workspaces in package.json"

    def test_at_least_two_packages(self):
        """Demo must have at least two workspace packages."""
        demo = os.path.join(self.REPO_DIR, self.DEMO_DIR)
        # Look for packages in packages/ or apps/ directories
        pkg_dirs = []
        for subdir in ("packages", "apps", "libs"):
            parent = os.path.join(demo, subdir)
            if os.path.isdir(parent):
                for name in os.listdir(parent):
                    if os.path.isdir(os.path.join(parent, name)):
                        pkg_json = os.path.join(parent, name, "package.json")
                        if os.path.isfile(pkg_json):
                            pkg_dirs.append(name)
        assert len(pkg_dirs) >= 2, f"Only {len(pkg_dirs)} package(s) found: {pkg_dirs}"

    # ------------------------------------------------------------------
    # L2: Pipeline configuration
    # ------------------------------------------------------------------

    def test_pipeline_has_build_task(self):
        """turbo.json must define a build pipeline task."""
        content = self._read(self.DEMO_DIR, "turbo.json")
        data = json.loads(content)
        pipeline = data.get("pipeline", data.get("tasks", {}))
        assert "build" in pipeline, "turbo.json missing build task in pipeline"

    def test_pipeline_has_dependencies(self):
        """Build task should have dependsOn for dependency ordering."""
        content = self._read(self.DEMO_DIR, "turbo.json")
        data = json.loads(content)
        pipeline = data.get("pipeline", data.get("tasks", {}))
        build = pipeline.get("build", {})
        assert (
            "dependsOn" in build or "cache" in build
        ), "Build task has no dependsOn or cache config"

    def test_pipeline_configures_outputs(self):
        """Pipeline should configure cache output directories."""
        content = self._read(self.DEMO_DIR, "turbo.json")
        data = json.loads(content)
        pipeline = data.get("pipeline", data.get("tasks", {}))
        build = pipeline.get("build", {})
        assert "outputs" in build, "Build task has no outputs configured"

    # ------------------------------------------------------------------
    # L2: Shared package
    # ------------------------------------------------------------------

    def test_shared_package_exists(self):
        """A shared library package must exist."""
        demo = os.path.join(self.REPO_DIR, self.DEMO_DIR)
        found = False
        for subdir in ("packages", "libs"):
            parent = os.path.join(demo, subdir)
            if os.path.isdir(parent):
                for name in os.listdir(parent):
                    pkg_json = os.path.join(parent, name, "package.json")
                    if os.path.isfile(pkg_json):
                        found = True
                        break
        assert found, "No shared library package found"

    def test_inter_package_dependency(self):
        """At least one package must depend on the shared package."""
        demo = os.path.join(self.REPO_DIR, self.DEMO_DIR)
        # Collect all package names
        pkg_names = set()
        all_deps = []
        for subdir in ("packages", "apps", "libs"):
            parent = os.path.join(demo, subdir)
            if not os.path.isdir(parent):
                continue
            for name in os.listdir(parent):
                pkg_json_path = os.path.join(parent, name, "package.json")
                if os.path.isfile(pkg_json_path):
                    with open(pkg_json_path, "r", errors="ignore") as fh:
                        data = json.loads(fh.read())
                    pkg_names.add(data.get("name", ""))
                    deps = {
                        **data.get("dependencies", {}),
                        **data.get("devDependencies", {}),
                    }
                    all_deps.append(deps)
        # Check if any package depends on another workspace package
        has_dep = False
        for deps in all_deps:
            for dep_name in deps:
                if dep_name in pkg_names:
                    has_dep = True
                    break
        assert has_dep, "No inter-package dependency found between workspace packages"

    # ------------------------------------------------------------------
    # L2: Build scripts
    # ------------------------------------------------------------------

    def test_packages_have_build_scripts(self):
        """Each workspace package must have a build script."""
        demo = os.path.join(self.REPO_DIR, self.DEMO_DIR)
        packages_without_build = []
        for subdir in ("packages", "apps", "libs"):
            parent = os.path.join(demo, subdir)
            if not os.path.isdir(parent):
                continue
            for name in os.listdir(parent):
                pkg_json = os.path.join(parent, name, "package.json")
                if os.path.isfile(pkg_json):
                    with open(pkg_json, "r", errors="ignore") as fh:
                        data = json.loads(fh.read())
                    if "build" not in data.get("scripts", {}):
                        packages_without_build.append(name)
        assert (
            not packages_without_build
        ), f"Packages without build script: {packages_without_build}"
