"""
Test for 'add-malli-schemas' skill — Clojure Malli Schema Definitions
Validates Malli schema source files, deps.edn dependency, validation middleware,
schema syntax (:map, :optional), humanize error formatting, coercion transformers,
and test file assertions.
"""

import glob
import os
import re

import pytest


class TestAddMalliSchemas:
    """Verify Malli schema definitions, middleware, and test coverage in a Clojure project."""

    REPO_DIR = "/workspace/metabase"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _find_schema_file(self) -> str:
        """Locate the Malli schema source file."""
        candidates = [
            os.path.join(self.REPO_DIR, "src", "myapp", "schemas.cljc"),
            os.path.join(self.REPO_DIR, "src", "myapp", "schemas.clj"),
        ]
        # Also search recursively for any schemas.cljc
        found = glob.glob(os.path.join(self.REPO_DIR, "src", "**", "schemas.cljc"), recursive=True)
        found += glob.glob(os.path.join(self.REPO_DIR, "src", "**", "schemas.clj"), recursive=True)
        for c in candidates + found:
            if os.path.isfile(c):
                return c
        return candidates[0]  # return expected path for assertion

    def _find_validation_middleware(self) -> str:
        """Locate validation middleware file."""
        candidates = [
            os.path.join(self.REPO_DIR, "src", "myapp", "middleware", "validation.clj"),
        ]
        found = glob.glob(os.path.join(self.REPO_DIR, "src", "**", "validation.clj"), recursive=True)
        for c in candidates + found:
            if os.path.isfile(c):
                return c
        return candidates[0]

    # ── file_path_check ──────────────────────────────────────────────────

    def test_schemas_source_file_exists(self):
        """Malli schema source file must exist."""
        schema_file = self._find_schema_file()
        assert os.path.isfile(schema_file), f"Schema file not found (tried {schema_file})"
        assert os.path.getsize(schema_file) > 0

    def test_deps_edn_with_malli_dependency(self):
        """deps.edn must exist and include metosin/malli dependency."""
        deps_path = os.path.join(self.REPO_DIR, "deps.edn")
        if not os.path.isfile(deps_path):
            # Try project.clj as alternative
            deps_path = os.path.join(self.REPO_DIR, "project.clj")
        assert os.path.isfile(deps_path), "Neither deps.edn nor project.clj found"
        content = self._read_file(deps_path)
        assert "metosin/malli" in content, "metosin/malli dependency not found"

    def test_validation_middleware_file_exists(self):
        """Validation middleware file must exist for ring request validation."""
        path = self._find_validation_middleware()
        assert os.path.isfile(path), f"{path} does not exist"
        assert os.path.getsize(path) > 0

    # ── semantic_check ───────────────────────────────────────────────────

    def test_schema_uses_malli_map_syntax(self):
        """Schema must use [:map ...] syntax with malli.core namespace import."""
        schema_file = self._find_schema_file()
        if not os.path.isfile(schema_file):
            pytest.skip("schema file not found")
        content = self._read_file(schema_file)
        assert "malli.core" in content or "malli.core :as m" in content, \
            "malli.core namespace import not found"
        assert "[:map" in content, "[:map schema definition pattern not found"

    def test_humanize_error_formatting_present(self):
        """Middleware must use me/humanize for human-readable error messages."""
        path = self._find_validation_middleware()
        if not os.path.isfile(path):
            pytest.skip("validation middleware not found")
        content = self._read_file(path)
        assert "malli.error" in content, "malli.error namespace not imported"
        assert "humanize" in content, "humanize function not referenced"

    def test_coercion_transformer_configured(self):
        """Validation middleware must configure malli.transform for coercion."""
        path = self._find_validation_middleware()
        if not os.path.isfile(path):
            pytest.skip("validation middleware not found")
        content = self._read_file(path)
        assert "malli.transform" in content or "mt/" in content, \
            "malli.transform import or transformer reference not found"
        has_transformer = (
            "transformer" in content
            or "string-transformer" in content
            or "json-transformer" in content
        )
        assert has_transformer, "No transformer instantiation found"

    def test_schema_registry_defined(self):
        """Schema file should define registry for reusable schema references."""
        schema_file = self._find_schema_file()
        if not os.path.isfile(schema_file):
            pytest.skip("schema file not found")
        content = self._read_file(schema_file)
        has_registry = (
            "registry" in content
            or "mu/merge" in content
            or "def " in content  # def schema definition
        )
        assert has_registry, "No schema registry or named schema definition found"

    # ── functional_check (static source inspection) ──────────────────────

    def test_schema_has_required_typed_fields(self):
        """Schema [:map] must have at least one strongly-typed required field."""
        schema_file = self._find_schema_file()
        if not os.path.isfile(schema_file):
            pytest.skip("schema file not found")
        content = self._read_file(schema_file)
        assert "[:map" in content, "[:map definition not found"
        # Check for Malli primitive types
        types = [":string", ":int", ":uuid", ":boolean", ":keyword", ":double"]
        found = any(t in content for t in types)
        assert found, "No Malli primitive types found in schema fields"

    def test_missing_required_key_fails_validation(self):
        """Schema must have at least one required field (without {:optional true})."""
        schema_file = self._find_schema_file()
        if not os.path.isfile(schema_file):
            pytest.skip("schema file not found")
        content = self._read_file(schema_file)
        lines = content.splitlines()
        map_section = False
        has_required = False
        for line in lines:
            if "[:map" in line:
                map_section = True
            if map_section and re.search(r"\[:\w+", line):
                if "{:optional true}" not in line:
                    has_required = True
                    break
        assert has_required, "No required fields found in :map schema (all are optional)"

    def test_optional_key_present(self):
        """At least one field should be marked {:optional true}."""
        schema_file = self._find_schema_file()
        if not os.path.isfile(schema_file):
            pytest.skip("schema file not found")
        content = self._read_file(schema_file)
        assert "{:optional true}" in content, \
            "No {:optional true} field annotation found in schema"

    def test_test_file_has_validate_assertions(self):
        """Test file must contain m/validate or m/explain assertions."""
        candidates = [
            os.path.join(self.REPO_DIR, "test", "myapp", "schemas_test.clj"),
            os.path.join(self.REPO_DIR, "test", "myapp", "schemas_test.cljc"),
        ]
        found_files = glob.glob(
            os.path.join(self.REPO_DIR, "test", "**", "*schemas*test*"), recursive=True
        )
        all_candidates = candidates + found_files
        found = False
        for path in all_candidates:
            if os.path.isfile(path):
                content = self._read_file(path)
                if "validate" in content and "(is " in content:
                    found = True
                    break
        assert found, "No test file with m/validate assertions found"
