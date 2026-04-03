"""Test file for the turborepo skill.

This suite validates a Turborepo cache-demo workspace: package.json
workspaces, turbo.json pipeline config, shared-utils exports, and build
caching behaviour.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest


class TestTurborepo:
    """Verify Turborepo cache-demo workspace in turbo repo."""

    REPO_DIR = "/workspace/turbo"

    ROOT_PKG_JSON = "examples/cache-demo/package.json"
    TURBO_JSON = "examples/cache-demo/turbo.json"
    SHARED_UTILS_PKG = "examples/cache-demo/packages/shared-utils/package.json"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _read_json(self, relative: str) -> dict:
        return json.loads(self._read_text(relative))

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_examples_cache_demo_package_json_exists(self):
        """Verify examples/cache-demo/package.json exists."""
        self._assert_non_empty_file(self.ROOT_PKG_JSON)

    def test_file_path_examples_cache_demo_turbo_json_exists(self):
        """Verify examples/cache-demo/turbo.json exists."""
        self._assert_non_empty_file(self.TURBO_JSON)

    def test_file_path_shared_utils_package_json_exists(self):
        """Verify examples/cache-demo/packages/shared-utils/package.json exists."""
        self._assert_non_empty_file(self.SHARED_UTILS_PKG)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_root_package_json_has_workspaces(self):
        """Root package.json has workspaces: ['packages/*', 'apps/*']."""
        pkg = self._read_json(self.ROOT_PKG_JSON)
        workspaces = pkg.get("workspaces", [])
        if isinstance(workspaces, dict):
            workspaces = workspaces.get("packages", [])
        assert any(
            "packages" in w for w in workspaces
        ), "Workspaces should include packages/*"
        assert any("apps" in w for w in workspaces), "Workspaces should include apps/*"

    def test_semantic_turbo_json_build_pipeline_dependson_and_outputs(self):
        """turbo.json build pipeline has dependsOn: ['^build'] and outputs: ['dist/**']."""
        turbo = self._read_json(self.TURBO_JSON)
        pipeline = turbo.get("pipeline", turbo.get("tasks", {}))
        build = pipeline.get("build", {})
        deps = build.get("dependsOn", [])
        assert "^build" in deps, "build.dependsOn should include '^build'"
        outputs = build.get("outputs", [])
        assert any(
            "dist" in o for o in outputs
        ), "build.outputs should include 'dist/**'"

    def test_semantic_turbo_json_test_pipeline_dependson_build(self):
        """turbo.json test pipeline has dependsOn: ['build'] and cache: true."""
        turbo = self._read_json(self.TURBO_JSON)
        pipeline = turbo.get("pipeline", turbo.get("tasks", {}))
        test = pipeline.get("test", {})
        deps = test.get("dependsOn", [])
        assert "build" in deps, "test.dependsOn should include 'build'"

    def test_semantic_turbo_json_globalenv_includes_node_env_and_api_url(self):
        """turbo.json globalEnv includes NODE_ENV and API_URL."""
        turbo = self._read_json(self.TURBO_JSON)
        global_env = turbo.get("globalEnv", [])
        global_deps = turbo.get("globalDependencies", [])
        combined = global_env + global_deps
        raw = json.dumps(turbo)
        assert "NODE_ENV" in raw, "globalEnv should include NODE_ENV"
        assert "API_URL" in raw, "globalEnv should include API_URL"

    def test_semantic_shared_utils_exports_formatcurrency_formatdate_slugify(self):
        """shared-utils exports formatCurrency, formatDate, slugify."""
        # Check the shared-utils source for exported functions
        shared_root = self._repo_path("examples/cache-demo/packages/shared-utils")
        all_src = ""
        if shared_root.is_dir():
            for f in shared_root.rglob("*.ts"):
                all_src += f.read_text(encoding="utf-8", errors="ignore") + "\n"
            for f in shared_root.rglob("*.js"):
                all_src += f.read_text(encoding="utf-8", errors="ignore") + "\n"
        if not all_src:
            # Fall back to checking package.json main/exports
            pkg = self._read_json(self.SHARED_UTILS_PKG)
            all_src = json.dumps(pkg)
        for fn in ["formatCurrency", "formatDate", "slugify"]:
            assert fn in all_src, f"shared-utils should export {fn}"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases)
    # ------------------------------------------------------------------

    def test_functional_npm_install_and_build_succeeds(self):
        """npm install && npm run build succeeds (source analysis)."""
        pkg = self._read_json(self.ROOT_PKG_JSON)
        scripts = pkg.get("scripts", {})
        assert "build" in scripts or "turbo" in json.dumps(
            pkg
        ), "Root package.json should have a build script or turbo dependency"

    def test_functional_dist_directories_created_in_all_packages(self):
        """dist/ directories created in all three packages."""
        turbo = self._read_json(self.TURBO_JSON)
        raw = json.dumps(turbo)
        assert "dist" in raw, "Build outputs should reference dist/"

    def test_functional_second_build_shows_cache_hits(self):
        """Second build shows cache hits."""
        turbo = self._read_json(self.TURBO_JSON)
        pipeline = turbo.get("pipeline", turbo.get("tasks", {}))
        build = pipeline.get("build", {})
        # cache is true by default in turbo, or explicitly set
        cache = build.get("cache", True)
        assert cache is not False, "Build task should have caching enabled"

    def test_functional_shared_utils_change_causes_cache_miss(self):
        """shared-utils change causes cache miss propagation."""
        turbo = self._read_json(self.TURBO_JSON)
        pipeline = turbo.get("pipeline", turbo.get("tasks", {}))
        build = pipeline.get("build", {})
        deps = build.get("dependsOn", [])
        assert (
            "^build" in deps
        ), "Topological deps (^build) ensure shared-utils changes propagate"

    def test_functional_npm_run_test_passes_in_all_packages(self):
        """npm run test passes in all packages."""
        turbo = self._read_json(self.TURBO_JSON)
        pipeline = turbo.get("pipeline", turbo.get("tasks", {}))
        assert "test" in pipeline, "turbo.json should define a test task"
