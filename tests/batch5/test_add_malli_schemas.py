"""
Test for 'add-malli-schemas' skill — Metabase Malli Schema Definitions
Validates that the Agent implemented Malli schemas for Dashboard, Card,
and DashboardCard entities with proper registry integration and tests.
"""

import os
import re

import pytest


class TestAddMalliSchemas:
    """Verify Metabase Malli schema definitions."""

    REPO_DIR = "/workspace/metabase"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_malli_schema_source_files_exist(self):
        """Verify the 3 Malli schema .clj files exist."""
        candidates = [
            "src/metabase/models/dashboard_schema.clj",
            "src/metabase/models/card_schema.clj",
            "src/metabase/models/dashboard_card_schema.clj",
        ]
        found = []
        for rel in candidates:
            if os.path.isfile(os.path.join(self.REPO_DIR, rel)):
                found.append(rel)
        # Also search broadly for schema files just in case naming differs
        if len(found) < 2:
            for dirpath, _, fnames in os.walk(os.path.join(self.REPO_DIR, "src")):
                for f in fnames:
                    if f.endswith(".clj") and "schema" in f.lower():
                        found.append(
                            os.path.relpath(os.path.join(dirpath, f), self.REPO_DIR)
                        )
        assert (
            len(found) >= 2
        ), f"Expected at least 2 Malli schema .clj files, found: {found}"

    def test_malli_test_files_exist(self):
        """Verify at least one test file for the schemas exists."""
        test_dir = os.path.join(self.REPO_DIR, "test")
        if not os.path.isdir(test_dir):
            pytest.skip("test/ directory not found in repo")
        test_files = []
        for dirpath, _, fnames in os.walk(test_dir):
            for f in fnames:
                if f.endswith(".clj") and "schema" in f.lower():
                    test_files.append(f)
        assert test_files, "No Malli schema test files found under test/"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_dashboard_schema_uses_map(self):
        """Verify Dashboard schema uses [:map ...] Malli notation."""
        schema_files = self._find_schema_files("dashboard")
        assert schema_files, "No dashboard schema file found"
        content = self._read_first(schema_files)
        assert re.search(
            r"\[:map", content
        ), "Dashboard schema does not use [:map ...] Malli notation"

    def test_card_schema_uses_multi_dispatch(self):
        """Verify Card schema uses [:multi {:dispatch :type}] for polymorphism."""
        schema_files = self._find_schema_files("card")
        assert schema_files, "No card schema file found"
        content = self._read_first(schema_files)
        assert (
            ":multi" in content or ":dispatch" in content
        ), "Card schema does not use [:multi {:dispatch ...}]"

    def test_dashboard_card_has_position_fields(self):
        """Verify DashboardCard schema includes :row, :col, :size_x, :size_y."""
        schema_files = self._find_schema_files("dashboard_card")
        if not schema_files:
            schema_files = self._find_schema_files("dashcard")
        assert schema_files, "No dashboard-card schema file found"
        content = self._read_first(schema_files)
        for field in [":row", ":col", ":size_x", ":size_y"]:
            assert field in content, f"DashboardCard schema missing field {field}"

    def test_schema_registry_configured(self):
        """Verify schema registry is set up (set-default-registry! or malli.registry)."""
        src_dir = os.path.join(self.REPO_DIR, "src")
        found = False
        for dirpath, _, fnames in os.walk(src_dir):
            for f in fnames:
                if f.endswith(".clj"):
                    fpath = os.path.join(dirpath, f)
                    with open(fpath, "r", errors="ignore") as fh:
                        if "registry" in fh.read():
                            found = True
                            break
            if found:
                break
        assert found, "No reference to malli registry found in source files"

    # ── functional_check ────────────────────────────────────────────────────

    def test_schema_files_are_valid_clojure(self):
        """Verify each schema .clj file is at least syntactically balanced (parens)."""
        schema_files = self._find_all_schema_files()
        assert schema_files, "No schema .clj files found"
        for fpath in schema_files:
            with open(fpath, "r", errors="ignore") as fh:
                content = fh.read()
            opens = content.count("(") + content.count("[") + content.count("{")
            closes = content.count(")") + content.count("]") + content.count("}")
            assert opens == closes, (
                f"Unbalanced brackets in {os.path.basename(fpath)}: "
                f"open={opens}, close={closes}"
            )

    def test_dashboard_schema_has_namespace(self):
        """Verify dashboard schema file declares a Clojure namespace."""
        schema_files = self._find_schema_files("dashboard")
        assert schema_files, "No dashboard schema file found"
        content = self._read_first(schema_files)
        assert re.search(
            r"\(ns\s+", content
        ), "Dashboard schema file does not declare a namespace"

    def test_card_schema_has_namespace(self):
        """Verify card schema file declares a Clojure namespace."""
        schema_files = self._find_schema_files("card")
        assert schema_files, "No card schema file found"
        content = self._read_first(schema_files)
        assert re.search(
            r"\(ns\s+", content
        ), "Card schema file does not declare a namespace"

    def test_test_files_reference_schemas(self):
        """Verify test files actually reference the schema modules."""
        test_dir = os.path.join(self.REPO_DIR, "test")
        if not os.path.isdir(test_dir):
            pytest.skip("test/ directory not found")
        found = False
        for dirpath, _, fnames in os.walk(test_dir):
            for f in fnames:
                if f.endswith(".clj") and "schema" in f.lower():
                    fpath = os.path.join(dirpath, f)
                    with open(fpath, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "schema" in content and (
                        "deftest" in content or "testing" in content
                    ):
                        found = True
                        break
            if found:
                break
        assert found, "No test file references schemas with deftest/testing"

    def test_malli_schema_defines_required_fields(self):
        """Verify at least one schema defines required fields (non-optional)."""
        schema_files = self._find_all_schema_files()
        assert schema_files, "No schema files found"
        for fpath in schema_files:
            with open(fpath, "r", errors="ignore") as fh:
                content = fh.read()
            # Malli required fields typically appear as bare keywords inside [:map ...]
            if re.search(r"\[:map.*\[:\w+", content, re.DOTALL):
                return  # pass
        pytest.fail("No schema defines required fields in [:map ...] notation")

    def test_schemas_import_malli(self):
        """Verify schema files import the malli library."""
        schema_files = self._find_all_schema_files()
        assert schema_files, "No schema files found"
        for fpath in schema_files:
            with open(fpath, "r", errors="ignore") as fh:
                content = fh.read()
            if "malli" in content:
                return  # pass
        pytest.fail("No schema file imports malli")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_schema_files(self, keyword):
        src_dir = os.path.join(self.REPO_DIR, "src")
        results = []
        if not os.path.isdir(src_dir):
            return results
        for dirpath, _, fnames in os.walk(src_dir):
            for f in fnames:
                if f.endswith(".clj") and keyword in f.lower():
                    results.append(os.path.join(dirpath, f))
        return results

    def _find_all_schema_files(self):
        src_dir = os.path.join(self.REPO_DIR, "src")
        results = []
        if not os.path.isdir(src_dir):
            return results
        for dirpath, _, fnames in os.walk(src_dir):
            for f in fnames:
                if f.endswith(".clj") and "schema" in f.lower():
                    results.append(os.path.join(dirpath, f))
        return results

    def _read_first(self, paths):
        with open(paths[0], "r", errors="ignore") as fh:
            return fh.read()
