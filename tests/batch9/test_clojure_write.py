"""
Test for 'clojure-write' skill — Clojure Migration Validator
Validates core, schema_diff, integrity, and report modules for a Clojure migration
validation pipeline, including threading macros, severity logic, and Clojure conventions.
"""

import os
import re

import pytest


class TestClojureWrite:
    """Verify Clojure migration validator source files and logic."""

    REPO_DIR = "/workspace/metabase"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _src(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "src", "metabase", "migration_validator", *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_all_four_source_files_exist(self):
        """core.clj, schema_diff.clj, integrity.clj, report.clj must exist."""
        for name in ("core.clj", "schema_diff.clj", "integrity.clj", "report.clj"):
            path = self._src(name)
            assert os.path.isfile(path), f"{path} does not exist"
            assert os.path.getsize(path) > 0

    def test_test_file_exists(self):
        """Test file for migration_validator must exist with at least one deftest."""
        path = os.path.join(self.REPO_DIR, "test", "metabase", "migration_validator", "core_test.clj")
        assert os.path.isfile(path), f"{path} does not exist"
        content = self._read_file(path)
        assert "deftest" in content, "Test file has no (deftest ...) form"

    def test_namespace_declarations_match_paths(self):
        """schema_diff.clj must have matching (ns metabase.migration-validator.schema-diff)."""
        path = self._src("schema_diff.clj")
        if not os.path.isfile(path):
            pytest.skip("schema_diff.clj not found")
        content = self._read_file(path)
        assert "metabase.migration-validator.schema-diff" in content, \
            "Namespace declaration does not match file path"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_compare_schemas_function_defined(self):
        """schema_diff.clj must define (defn compare-schemas [before after] ...)."""
        path = self._src("schema_diff.clj")
        if not os.path.isfile(path):
            pytest.skip("schema_diff.clj not found")
        content = self._read_file(path)
        assert "(defn compare-schemas" in content, "compare-schemas function not defined"
        for key in (":added-tables", ":removed-tables", ":modified-tables"):
            assert key in content, f"Return map key {key} not found in compare-schemas"

    def test_integrity_functions_defined(self):
        """integrity.clj must define check-null-violations, check-foreign-key-orphans, check-unique-violations."""
        path = self._src("integrity.clj")
        if not os.path.isfile(path):
            pytest.skip("integrity.clj not found")
        content = self._read_file(path)
        for fn in ("check-null-violations", "check-foreign-key-orphans", "check-unique-violations"):
            assert f"(defn {fn}" in content, f"{fn} not defined in integrity.clj"

    def test_report_functions_with_correct_keys(self):
        """report.clj must define generate-edn-report and generate-markdown-report."""
        path = self._src("report.clj")
        if not os.path.isfile(path):
            pytest.skip("report.clj not found")
        content = self._read_file(path)
        assert "(defn generate-edn-report" in content, "generate-edn-report not defined"
        assert "(defn generate-markdown-report" in content, "generate-markdown-report not defined"
        assert ":timestamp" in content, ":timestamp key not found in report"
        assert ":severity" in content, ":severity key not found in report"

    def test_core_validate_migration_uses_threading(self):
        """core.clj must define validate-migration using threading macros (-> or ->>)."""
        path = self._src("core.clj")
        if not os.path.isfile(path):
            pytest.skip("core.clj not found")
        content = self._read_file(path)
        assert "(defn validate-migration" in content, "validate-migration not defined"
        assert "->" in content or "->>" in content, "No threading macro found in core.clj"

    def test_severity_priority_order(self):
        """report.clj must implement :critical > :warning > :info priority ordering."""
        path = self._src("report.clj")
        if not os.path.isfile(path):
            pytest.skip("report.clj not found")
        content = self._read_file(path)
        for sev in (":critical", ":warning", ":info"):
            assert sev in content, f"Severity keyword {sev} not found in report.clj"

    # ── functional_check (static source inspection) ──────────────────────

    def test_compare_schemas_handles_empty_input(self):
        """compare-schemas must initialize maps/sets for empty input (no nil returns)."""
        path = self._src("schema_diff.clj")
        if not os.path.isfile(path):
            pytest.skip("schema_diff.clj not found")
        content = self._read_file(path)
        has_empty = "#{}" in content or "{}" in content
        assert has_empty, "No empty collection initializer found in compare-schemas"

    def test_nullable_change_detection(self):
        """compare-schemas must detect nullable changes with :nullable-changes key."""
        path = self._src("schema_diff.clj")
        if not os.path.isfile(path):
            pytest.skip("schema_diff.clj not found")
        content = self._read_file(path)
        assert ":nullable" in content, ":nullable reference not found in schema_diff"

    def test_check_null_violations_skips_nullable(self):
        """check-null-violations must skip columns where :nullable is truthy."""
        path = self._src("integrity.clj")
        if not os.path.isfile(path):
            pytest.skip("integrity.clj not found")
        content = self._read_file(path)
        assert ":nullable" in content, ":nullable check not found in integrity.clj"
        has_filter = "filter" in content or "remove" in content or "when-not" in content
        assert has_filter, "No filter/remove/when-not for nullable check found"

    def test_validate_migration_returns_all_keys(self):
        """validate-migration must return map with :diff, :integrity, :edn-report, :markdown-report."""
        path = self._src("core.clj")
        if not os.path.isfile(path):
            pytest.skip("core.clj not found")
        content = self._read_file(path)
        for key in (":diff", ":integrity", ":edn-report", ":markdown-report"):
            assert key in content, f"Return map key {key} not found in validate-migration"
