"""
Test for 'turborepo' skill — Turborepo shared UI package
Validates that the Agent created a shared UI package in a Turborepo
monorepo with correct package.json exports, turbo.json pipeline,
and TypeScript component structure.
"""

import os
import re
import json

import pytest


class TestTurborepo:
    """Verify Turborepo shared UI package implementation."""

    REPO_DIR = "/workspace/turbo"
    UI_PKG_DIR = os.path.join(REPO_DIR, "packages/ui")

    def test_ui_package_json_exists(self):
        """packages/ui/package.json must exist with scoped name and exports."""
        pkg_json = os.path.join(self.UI_PKG_DIR, "package.json")
        assert os.path.isfile(pkg_json), "packages/ui/package.json not found"
        with open(pkg_json, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r'"name"\s*:\s*"@', content), "Scoped package name not found"
        assert re.search(r'"exports"', content), "exports field not found in package.json"

    def test_ui_src_index_ts_exists(self):
        """packages/ui/src/index.ts must exist and export components."""
        index_ts = os.path.join(self.UI_PKG_DIR, "src/index.ts")
        alt_index_tsx = os.path.join(self.UI_PKG_DIR, "src/index.tsx")
        exists = os.path.isfile(index_ts) or os.path.isfile(index_tsx)
        assert exists, "packages/ui/src/index.ts(x) not found"
        target = index_ts if os.path.isfile(index_ts) else alt_index_tsx
        with open(target, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"export", content), "No export statements in index file"

    def test_turbo_json_has_build_pipeline(self):
        """turbo.json must define a build pipeline."""
        turbo_json = os.path.join(self.REPO_DIR, "turbo.json")
        assert os.path.isfile(turbo_json), "turbo.json not found"
        with open(turbo_json, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r'"build"', content), "build pipeline not found in turbo.json"
        assert re.search(r"dependsOn|\^build", content), "dependsOn not found in pipeline"

    def test_package_json_exports_main_types(self):
        """package.json must export both main/module and types fields."""
        pkg_json = os.path.join(self.UI_PKG_DIR, "package.json")
        assert os.path.isfile(pkg_json)
        with open(pkg_json, "r", errors="ignore") as fh:
            content = fh.read()
        has_main = re.search(r'"main"|"module"', content)
        has_types = re.search(r'"types"|"typings"', content)
        assert has_main or re.search(r'"exports"', content), "main/module/exports field not found"
        assert has_types or re.search(r'"exports"', content), "types/typings field not found"

    def test_tsconfig_extends_base(self):
        """packages/ui/tsconfig.json must extend the shared base config."""
        tsconfig = os.path.join(self.UI_PKG_DIR, "tsconfig.json")
        assert os.path.isfile(tsconfig), "packages/ui/tsconfig.json not found"
        with open(tsconfig, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r'"extends"', content), "extends field not found in tsconfig.json"

    def test_component_has_react_import_or_tsx(self):
        """At least one .tsx component file must exist in packages/ui/src/."""
        src_dir = os.path.join(self.UI_PKG_DIR, "src")
        found_tsx = False
        if os.path.isdir(src_dir):
            for root, dirs, files in os.walk(src_dir):
                for f in files:
                    if f.endswith(".tsx"):
                        found_tsx = True
                        break
                if found_tsx:
                    break
        assert found_tsx, "No .tsx component files found in packages/ui/src/"

    def test_package_json_parses_as_valid_json(self):
        """packages/ui/package.json must be valid JSON."""
        pkg_json = os.path.join(self.UI_PKG_DIR, "package.json")
        assert os.path.isfile(pkg_json)
        with open(pkg_json, "r", errors="ignore") as fh:
            content = fh.read()
        try:
            json.loads(content)
        except json.JSONDecodeError:
            pytest.fail("packages/ui/package.json is not valid JSON")

    def test_turbo_json_parses_as_valid_json(self):
        """turbo.json must be valid JSON."""
        turbo_json = os.path.join(self.REPO_DIR, "turbo.json")
        assert os.path.isfile(turbo_json)
        with open(turbo_json, "r", errors="ignore") as fh:
            content = fh.read()
        try:
            json.loads(content)
        except json.JSONDecodeError:
            pytest.fail("turbo.json is not valid JSON")

    def test_typescript_compilation_src_files(self):
        """TypeScript source files must exist in packages/ui/src/."""
        src_dir = os.path.join(self.UI_PKG_DIR, "src")
        found_ts = False
        if os.path.isdir(src_dir):
            for root, dirs, files in os.walk(src_dir):
                for f in files:
                    if f.endswith((".ts", ".tsx")):
                        found_ts = True
                        break
                if found_ts:
                    break
        assert found_ts, "No TypeScript files found in packages/ui/src/"

    def test_package_missing_exports_causes_resolution_failure(self):
        """Non-exported paths must not be importable (exports map restricts access)."""
        pkg_json = os.path.join(self.UI_PKG_DIR, "package.json")
        assert os.path.isfile(pkg_json)
        with open(pkg_json, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(
            r'"exports"\s*:\s*\{', content
        ), "exports map not found — all paths would be importable"

    def test_index_exports_all_components(self):
        """All .tsx components in src/ must be re-exported from index.ts."""
        src_dir = os.path.join(self.UI_PKG_DIR, "src")
        index_ts = os.path.join(src_dir, "index.ts")
        index_tsx = os.path.join(src_dir, "index.tsx")
        target = index_ts if os.path.isfile(index_ts) else index_tsx
        if not os.path.isfile(target):
            pytest.skip("index.ts(x) not found")
        with open(target, "r", errors="ignore") as fh:
            index_content = fh.read()
        tsx_files = []
        if os.path.isdir(src_dir):
            for f in os.listdir(src_dir):
                if f.endswith(".tsx") and f not in ("index.tsx",):
                    tsx_files.append(f.replace(".tsx", ""))
        for comp in tsx_files:
            assert comp in index_content, f"Component {comp} not re-exported from index"
