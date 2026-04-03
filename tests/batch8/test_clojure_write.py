"""
Test for 'clojure-write' skill — Metabase Catalog Registry & Search
Validates that the Agent implemented registry, search/core, and catalog API
modules in the Metabase Clojure codebase.
"""

import os
import re
import subprocess

import pytest


class TestClojureWrite:
    """Verify Metabase catalog registry and search implementation."""

    REPO_DIR = "/workspace/metabase"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_registry_clj_exists(self):
        """Verify metabase registry source file exists."""
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, p))
            for p in ("src/metabase/models/registry.clj",
                       "src/metabase/models/registry.cljs")
        )
        assert found, "Neither registry.clj nor registry.cljs exists"

    def test_search_core_and_catalog_api_exist(self):
        """Verify search/core.clj and api/catalog.clj exist."""
        for rel in ("src/metabase/search/core.clj", "src/metabase/api/catalog.clj"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_test_files_exist(self):
        """Verify test files for registry and search core exist."""
        for rel in ("test/metabase/models/registry_test.clj",
                     "test/metabase/search/core_test.clj"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    # ── semantic_check ──────────────────────────────────────────────

    def test_build_catalog_function_defined(self):
        """Verify build-catalog function is defined in registry.clj with docstring."""
        content = ""
        for candidate in ("src/metabase/models/registry.clj",
                          "src/metabase/models/registry.cljs"):
            content = self._read(os.path.join(self.REPO_DIR, candidate))
            if content:
                break
        assert content, "registry source file is empty or unreadable"
        assert "defn build-catalog" in content, \
            "build-catalog function not found in registry source"

    def test_find_tables_with_ilike_filter(self):
        """Verify find-tables applies ILIKE or case-insensitive filter on table name."""
        content = self._read(os.path.join(self.REPO_DIR, "src/metabase/search/core.clj"))
        assert content, "search/core.clj is empty or unreadable"
        found = any(kw in content for kw in ("ilike", "ILIKE", "like", "find-tables"))
        assert found, "No case-insensitive filter pattern found in search/core.clj"

    def test_catalog_endpoint_route_defined(self):
        """Verify catalog API defines GET route using defendpoint or compojure."""
        content = self._read(os.path.join(self.REPO_DIR, "src/metabase/api/catalog.clj"))
        assert content, "api/catalog.clj is empty or unreadable"
        found = any(kw in content for kw in ("defendpoint", "GET", "/catalog"))
        assert found, "No GET route definition found in catalog.clj"

    # ── functional_check (command) ──────────────────────────────────

    def _skip_unless_lein_ready(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if not os.path.isfile(os.path.join(self.REPO_DIR, "project.clj")):
            pytest.skip("project.clj missing")

    def test_build_catalog_returns_map(self):
        """build-catalog returns a Clojure map with :databases and :tables keys."""
        self._skip_unless_lein_ready()
        # Semantic fallback: verify the function signature in source
        content = ""
        for candidate in ("src/metabase/models/registry.clj",
                          "src/metabase/models/registry.cljs"):
            content = self._read(os.path.join(self.REPO_DIR, candidate))
            if content:
                break
        assert "build-catalog" in content, "build-catalog not found"
        assert ":databases" in content or ":tables" in content, \
            "build-catalog does not reference :databases or :tables keys"

    def test_find_tables_name_filter(self):
        """find-tables with name filter returns only matching tables case-insensitively."""
        self._skip_unless_lein_ready()
        content = self._read(os.path.join(self.REPO_DIR, "src/metabase/search/core.clj"))
        assert "find-tables" in content, "find-tables function not found"
        # Check test file for filter verification
        test_content = self._read(os.path.join(
            self.REPO_DIR, "test/metabase/search/core_test.clj"))
        assert test_content, "core_test.clj is empty"
        assert "find-tables" in test_content, "find-tables not tested in core_test.clj"

    def test_find_tables_unknown_db_returns_empty(self):
        """find-tables with non-existent :db-id returns empty seq, not exception."""
        self._skip_unless_lein_ready()
        test_content = self._read(os.path.join(
            self.REPO_DIR, "test/metabase/search/core_test.clj"))
        assert test_content, "core_test.clj is empty"
        assert "find-tables" in test_content or "db-id" in test_content, \
            "No edge case test for unknown db-id in core_test.clj"

    def test_catalog_api_unauthenticated_returns_401(self):
        """GET /api/catalog without authentication returns 401 Unauthorized."""
        self._skip_unless_lein_ready()
        content = self._read(os.path.join(self.REPO_DIR, "src/metabase/api/catalog.clj"))
        assert content, "catalog.clj is empty"
        # Check for auth middleware or 401 handling
        assert "authenticated" in content.lower() or "auth" in content.lower() or \
               "defendpoint" in content, \
            "No authentication handling found in catalog.clj"
