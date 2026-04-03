"""
Test for 'turborepo' skill — Turborepo Monorepo Build System
Validates turbo.json configuration, pipeline dependencies, output globs,
workspaces field, and package name uniqueness in a Turborepo monorepo.
"""

import glob
import json
import os

import pytest


class TestTurborepo:
    """Verify Turborepo monorepo configuration and workspace structure."""

    REPO_DIR = "/workspace/turbo"

    # ── helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _load_turbo_json(self) -> dict:
        path = os.path.join(self.REPO_DIR, "turbo.json")
        with open(path, "r") as fh:
            return json.load(fh)

    def _load_root_package_json(self) -> dict:
        path = os.path.join(self.REPO_DIR, "package.json")
        with open(path, "r") as fh:
            return json.load(fh)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_turbo_json_and_root_package_json_exist(self):
        """turbo.json and package.json must exist at repo root and be valid JSON."""
        for name in ("turbo.json", "package.json"):
            path = os.path.join(self.REPO_DIR, name)
            assert os.path.isfile(path), f"{path} does not exist"
            with open(path) as f:
                json.load(f)  # must parse without error

    def test_packages_directory_with_workspace_packages(self):
        """packages/ must contain at least one sub-package with package.json."""
        pkg_jsons = glob.glob(os.path.join(self.REPO_DIR, "packages", "*", "package.json"))
        assert len(pkg_jsons) >= 1, "No packages/*/package.json found"

    def test_env_example_with_turbo_token_placeholder(self):
        """.env.example must exist with TURBO_TOKEN placeholder."""
        candidates = [
            os.path.join(self.REPO_DIR, ".env.example"),
            os.path.join(self.REPO_DIR, ".env.turbo.example"),
        ]
        found = None
        for c in candidates:
            if os.path.isfile(c):
                found = c
                break
        assert found is not None, "No .env.example or .env.turbo.example found"
        content = self._read_file(found)
        assert "TURBO_TOKEN" in content, "TURBO_TOKEN placeholder not in .env.example"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_turbo_json_build_depends_on_caret_build(self):
        """turbo.json pipeline.build.dependsOn must contain '^build'."""
        config = self._load_turbo_json()
        pipeline = config.get("pipeline", config.get("tasks", {}))
        build = pipeline.get("build", {})
        deps = build.get("dependsOn", [])
        assert "^build" in deps, f"'^build' not in build.dependsOn: {deps}"

    def test_turbo_json_test_depends_on_build(self):
        """turbo.json pipeline.test.dependsOn must contain 'build'."""
        config = self._load_turbo_json()
        pipeline = config.get("pipeline", config.get("tasks", {}))
        test_cfg = pipeline.get("test", {})
        deps = test_cfg.get("dependsOn", [])
        assert "build" in deps, f"'build' not in test.dependsOn: {deps}"

    def test_build_outputs_configured_with_dist_glob(self):
        """pipeline.build.outputs must include 'dist/**' or '.next/**'."""
        config = self._load_turbo_json()
        pipeline = config.get("pipeline", config.get("tasks", {}))
        outputs = pipeline.get("build", {}).get("outputs", [])
        valid = any("dist/**" in o or ".next/**" in o for o in outputs)
        assert valid, f"Build outputs missing dist/**/. next/**: {outputs}"

    def test_turbo_token_not_hardcoded_in_turbo_json(self):
        """TURBO_TOKEN must not be hardcoded in turbo.json."""
        content = self._read_file(os.path.join(self.REPO_DIR, "turbo.json"))
        # A hardcoded token would be a long alphanumeric string after "token"
        import re
        hardcoded = re.search(r'"token"\s*:\s*"[a-zA-Z0-9]{10,}"', content)
        assert not hardcoded, "TURBO_TOKEN appears hardcoded in turbo.json"

    # ── functional_check (import / json parsing) ─────────────────────────

    def test_turbo_json_is_valid_json_with_pipeline(self):
        """turbo.json must parse as JSON and contain 'pipeline' or 'tasks' key."""
        config = self._load_turbo_json()
        assert "pipeline" in config or "tasks" in config, (
            "turbo.json missing 'pipeline' or 'tasks' key"
        )

    def test_build_has_caret_build_in_depends_on_functional(self):
        """Programmatic: pipeline.build.dependsOn must contain '^build'."""
        config = self._load_turbo_json()
        pipeline = config.get("pipeline", config.get("tasks", {}))
        deps = pipeline.get("build", {}).get("dependsOn", [])
        assert "^build" in deps

    def test_all_package_names_are_unique(self):
        """All packages/*/package.json must have unique 'name' fields."""
        pkg_jsons = glob.glob(
            os.path.join(self.REPO_DIR, "packages", "*", "package.json")
        )
        names = []
        for pj in pkg_jsons:
            with open(pj) as f:
                pkg = json.load(f)
            names.append(pkg.get("name", ""))
        assert len(names) == len(set(names)), f"Duplicate package names: {names}"

    def test_root_package_json_has_workspaces_field(self):
        """Root package.json must declare 'workspaces' field."""
        pkg = self._load_root_package_json()
        assert "workspaces" in pkg, "Root package.json missing 'workspaces' field"

    def test_duplicate_package_name_detection_logic(self):
        """Duplicate detection logic must catch duplicates correctly."""
        names = ["@repo/ui", "@repo/config", "@repo/ui"]
        assert len(names) != len(set(names)), "Duplicate detection failed"
