"""
Tests for turborepo skill.
REPO_DIR: /workspace/turbo
"""

import os
import json
import glob
import pytest

REPO_DIR = "/workspace/turbo"


def _path(rel):
    return os.path.join(REPO_DIR, rel)


def _read(rel):
    with open(_path(rel), encoding="utf-8") as f:
        return f.read()


def _load_json(rel):
    with open(_path(rel), encoding="utf-8") as f:
        return json.load(f)


class TestTurborepo:
    # ── file_path_check ────────────────────────────────────────────────────
    def test_root_turbo_json_exists(self):
        """Verify root turbo.json exists at workspace root and is valid JSON."""
        fpath = _path("turbo.json")
        assert os.path.isfile(fpath), "turbo.json must exist at workspace root"
        # Validate JSON
        data = _load_json("turbo.json")
        assert isinstance(data, dict), "turbo.json must be a valid JSON object"

    def test_root_package_json_exists(self):
        """Verify root package.json exists with workspaces configuration."""
        fpath = _path("package.json")
        assert os.path.isfile(fpath), "root package.json must exist"
        data = _load_json("package.json")
        assert isinstance(data, dict), "root package.json must be valid JSON"
        assert "workspaces" in data, "root package.json must contain 'workspaces' field"

    # ── semantic_check ─────────────────────────────────────────────────────
    def test_build_depends_on_upstream(self):
        """Verify build task has dependsOn: ['^build'] for upstream dependency."""
        data = _load_json("turbo.json")
        # turbo.json uses either "pipeline" (v1) or "tasks" (v2) key
        tasks = data.get("pipeline") or data.get("tasks") or {}
        assert "build" in tasks, "build task must be defined in turbo.json"
        build_task = tasks["build"]
        depends_on = build_task.get("dependsOn", [])
        assert (
            "^build" in depends_on
        ), "build.dependsOn must contain '^build' for upstream dependency ordering"

    def test_dev_task_has_cache_false_and_persistent(self):
        """Verify dev task has cache: false and persistent: true."""
        data = _load_json("turbo.json")
        tasks = data.get("pipeline") or data.get("tasks") or {}
        assert "dev" in tasks, "dev task must be defined in turbo.json"
        dev_task = tasks["dev"]
        assert dev_task.get("cache") is False, "dev task must have 'cache': false"
        assert (
            dev_task.get("persistent") is True
        ), "dev task must have 'persistent': true"

    def test_all_four_tasks_defined(self):
        """Verify build, test, lint, and dev tasks all defined in turbo.json."""
        data = _load_json("turbo.json")
        tasks = data.get("pipeline") or data.get("tasks") or {}
        for task_name in ["build", "test", "lint", "dev"]:
            assert (
                task_name in tasks
            ), f"'{task_name}' task must be defined in turbo.json"

    def test_ui_package_storybook_env(self):
        """Verify ui package turbo config adds STORYBOOK_ENV to environment passthrough."""
        ui_turbo = _path("packages/ui/turbo.json")
        ui_pkg = _path("packages/ui/package.json")
        if not os.path.isfile(ui_turbo) and not os.path.isfile(ui_pkg):
            pytest.skip("packages/ui/ not found; skipping ui-specific env check")
        if os.path.isfile(ui_turbo):
            content = _read("packages/ui/turbo.json")
            assert (
                "STORYBOOK_ENV" in content
            ), "ui package turbo.json must declare STORYBOOK_ENV in env passthrough"
        else:
            content = _read("packages/ui/package.json")
            assert (
                "STORYBOOK_ENV" in content
            ), "ui package.json must reference STORYBOOK_ENV"

    def test_web_excludes_next_cache(self):
        """Verify web package excludes .next/cache/** from turbo outputs."""
        web_turbo = _path("apps/web/turbo.json")
        if not os.path.isfile(web_turbo):
            pytest.skip(
                "apps/web/turbo.json not found; skipping Next.js cache exclusion check"
            )
        content = _read("apps/web/turbo.json")
        assert (
            "!.next/cache/**" in content
        ), "web app must exclude '!.next/cache/**' from turbo outputs"

    # ── functional_check ──────────────────────────────────────────────────
    def test_workspace_protocol_in_package_json(self):
        """Verify workspace packages reference each other using workspace:* protocol."""
        candidates = [
            _path("apps/web/package.json"),
            _path("apps/docs/package.json"),
        ]
        found_workspace_protocol = False
        for fpath in candidates:
            if os.path.isfile(fpath):
                with open(fpath, encoding="utf-8") as fh:
                    content = fh.read()
                if "workspace:*" in content or "workspace:" in content:
                    found_workspace_protocol = True
                    break
        # Fallback: scan all package.json files
        if not found_workspace_protocol:
            for fpath in glob.glob(
                os.path.join(REPO_DIR, "**/package.json"), recursive=True
            ):
                if "node_modules" in fpath:
                    continue
                with open(fpath, encoding="utf-8") as fh:
                    content = fh.read()
                if "workspace:*" in content or "workspace:" in content:
                    found_workspace_protocol = True
                    break
        assert (
            found_workspace_protocol
        ), "At least one package.json must use 'workspace:*' for internal dependency"

    def test_root_turbo_json_is_valid_json(self):
        """Verify turbo.json is parseable as valid JSON."""
        data = _load_json("turbo.json")
        assert isinstance(data, dict), "turbo.json must be a valid JSON object"
        assert len(data) > 0, "turbo.json must not be an empty JSON object"

    def test_all_package_jsons_valid(self):
        """Verify all package.json files in apps/ and packages/ are valid JSON."""
        pkg_files = glob.glob(os.path.join(REPO_DIR, "**/package.json"), recursive=True)
        parsed = 0
        for fpath in pkg_files:
            if "node_modules" in fpath:
                continue
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)  # raises if invalid
            assert isinstance(data, dict), f"{fpath} must be a JSON object"
            parsed += 1
        assert parsed > 0, "At least one package.json must exist and be parseable"

    def test_lint_task_no_build_cache_dependency(self):
        """Verify lint task does not declare dependsOn ^build."""
        data = _load_json("turbo.json")
        tasks = data.get("pipeline") or data.get("tasks") or {}
        assert "lint" in tasks, "lint task must be defined in turbo.json"
        lint_task = tasks["lint"]
        depends_on = lint_task.get("dependsOn", [])
        assert (
            "^build" not in depends_on
        ), "lint task must NOT depend on '^build' to enable fast parallel linting"

    def test_build_outputs_include_dist_or_build(self):
        """Verify build task outputs includes dist/** or build/** or .next/** for caching."""
        data = _load_json("turbo.json")
        tasks = data.get("pipeline") or data.get("tasks") or {}
        assert "build" in tasks, "build task must be defined"
        build_task = tasks["build"]
        outputs = build_task.get("outputs", [])
        assert len(outputs) > 0, "build task must define output glob patterns"
        valid_outputs = any(
            "dist/**" in o or "build/**" in o or ".next/**" in o for o in outputs
        )
        assert (
            valid_outputs
        ), "build outputs must contain 'dist/**' or 'build/**' or '.next/**' for turbo cache to work"
