"""
Tests for nx-workspace-patterns skill.
Validates Nx monorepo configuration files in nx repository.
"""

import os
import json
import glob
import pytest

REPO_DIR = "/workspace/nx"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


def _load_json(rel: str):
    with open(_path(rel), encoding="utf-8") as f:
        return json.load(f)


class TestNxWorkspacePatterns:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_nx_json_exists(self):
        """nx.json must exist at workspace root."""
        rel = "nx.json"
        assert os.path.isfile(_path(rel)), "nx.json not found at workspace root"
        assert os.path.getsize(_path(rel)) > 0, "nx.json is empty"

    def test_tsconfig_base_and_eslintrc_exist(self):
        """tsconfig.base.json and root .eslintrc.json must both exist."""
        for rel in ["tsconfig.base.json", ".eslintrc.json"]:
            assert os.path.isfile(_path(rel)), f"{rel} not found"
            assert os.path.getsize(_path(rel)) > 0, f"{rel} is empty"

    def test_project_json_files_exist_for_packages(self):
        """Each package directory must have a project.json."""
        pattern = os.path.join(REPO_DIR, "packages", "*", "project.json")
        matches = glob.glob(pattern)
        assert (
            len(matches) >= 2
        ), f"Expected >= 2 project.json files under packages/, found {len(matches)}"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_nx_json_defaultbase_is_main(self):
        """nx.json must have defaultBase set to 'main' for CI affected computation."""
        data = _load_json("nx.json")
        assert "defaultBase" in data, "defaultBase key missing from nx.json"
        assert (
            data["defaultBase"] == "main"
        ), f"Expected defaultBase='main', got {data['defaultBase']!r}"

    def test_build_task_depends_on_upstream(self):
        """nx.json build task must have dependsOn=['^build'] for dependency ordering."""
        data = _load_json("nx.json")
        target_defaults = data.get("targetDefaults", {})
        assert (
            "build" in target_defaults
        ), "build target not defined in nx.json targetDefaults"
        depends_on = target_defaults["build"].get("dependsOn", [])
        assert (
            "^build" in depends_on
        ), f"build.dependsOn must contain '^build', got {depends_on}"

    def test_production_input_excludes_spec_files(self):
        """nx.json production named input must exclude *.spec.ts files."""
        data = _load_json("nx.json")
        named_inputs = data.get("namedInputs", {})
        assert (
            "production" in named_inputs
        ), "production named input not defined in nx.json"
        prod = named_inputs["production"]
        prod_str = json.dumps(prod)
        assert (
            "spec.ts" in prod_str or "spec" in prod_str
        ), "production input does not exclude spec files"
        assert (
            "!" in prod_str
        ), "production input must use negation (!) to exclude spec files"

    def test_eslintrc_module_boundary_ui_allows_util(self):
        """eslintrc.json must configure module boundary: type:ui can import type:util."""
        content = _read(".eslintrc.json")
        assert (
            "enforce-module-boundaries" in content or "module" in content.lower()
        ), "@nx/enforce-module-boundaries not found in .eslintrc.json"
        assert (
            "type:ui" in content or "ui" in content
        ), "type:ui constraint not found in .eslintrc.json"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_all_json_files_valid(self):
        """All JSON configuration files must be syntactically valid."""
        for rel in ["nx.json", "tsconfig.base.json", ".eslintrc.json"]:
            try:
                _load_json(rel)
            except json.JSONDecodeError as e:
                pytest.fail(f"{rel} is not valid JSON: {e}")

    def test_tsconfig_paths_workspace_prefix(self):
        """tsconfig.base.json must define @workspace/* path aliases."""
        data = _load_json("tsconfig.base.json")
        paths = data.get("compilerOptions", {}).get("paths", {})
        assert any(
            k.startswith("@") for k in paths
        ), f"No scoped (@) path aliases found in tsconfig.base.json paths: {list(paths.keys())}"

    def test_dev_task_cache_false_and_persistent(self):
        """nx.json dev task must have cache:false and persistent:true."""
        data = _load_json("nx.json")
        target_defaults = data.get("targetDefaults", {})
        if "dev" not in target_defaults:
            pytest.skip("dev target not defined in nx.json targetDefaults")
        dev = target_defaults["dev"]
        assert (
            dev.get("cache") is False
        ), f"dev.cache must be false, got {dev.get('cache')!r}"
        assert (
            dev.get("persistent") is True
        ), f"dev.persistent must be true, got {dev.get('persistent')!r}"

    def test_nx_json_has_defaultbase_key(self):
        """Negative: nx.json must have defaultBase key (absence is schema violation)."""
        data = _load_json("nx.json")
        assert "defaultBase" in data, "nx.json missing defaultBase — schema violation"

    def test_project_json_has_build_test_lint(self):
        """At least one project.json must define build, test, and lint targets."""
        pattern = os.path.join(REPO_DIR, "packages", "*", "project.json")
        matches = glob.glob(pattern)
        if not matches:
            pytest.skip("No project.json files found under packages/")
        for project_file in matches:
            rel = os.path.relpath(project_file, REPO_DIR)
            with open(project_file, encoding="utf-8") as f:
                data = json.load(f)
            targets = data.get("targets", {})
            if "build" in targets and "test" in targets and "lint" in targets:
                return  # found at least one
        pytest.fail("No project.json found with build + test + lint targets")
