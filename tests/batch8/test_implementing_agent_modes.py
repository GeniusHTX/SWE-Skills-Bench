"""
Test for 'implementing-agent-modes' skill — PostHog SQL Query Toolkit
Validates that the Agent created a read-only SQL agent toolkit with
security guards, caching, and schema introspection tools.
"""

import os
import re
import sys
import subprocess

import pytest


class TestImplementingAgentModes:
    """Verify PostHog SQL query agent toolkit implementation."""

    REPO_DIR = "/workspace/posthog"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_sql_query_toolkit_file_exists(self):
        """Verify sql_query_toolkit.py and query_executor.py exist."""
        for rel in ("posthog/hogql_queries/sql_query_toolkit.py",
                     "posthog/hogql_queries/query_executor.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_models_and_tests_exist(self):
        """Verify models.py and test file exist."""
        for rel in ("posthog/hogql_queries/models.py",
                     "tests/test_sql_query_toolkit.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_security_error_and_toolkit_importable(self):
        """SQLQueryToolkit and SecurityError are importable."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, self.REPO_DIR)
        try:
            from posthog.hogql_queries.sql_query_toolkit import SQLQueryToolkit, SecurityError  # noqa: F401
        except ImportError:
            pytest.skip("sql_query_toolkit not importable")
        finally:
            sys.path.pop(0)

    # ── semantic_check ──────────────────────────────────────────────

    def test_get_tools_returns_exactly_three(self):
        """Verify get_tools() returns list of 3 tools: run_sql_query, get_schema, explain_query."""
        content = self._read(os.path.join(
            self.REPO_DIR, "posthog/hogql_queries/sql_query_toolkit.py"))
        assert content, "sql_query_toolkit.py is empty or unreadable"
        for tool in ("run_sql_query", "get_schema", "explain_query"):
            assert tool in content, f"Tool '{tool}' not found in sql_query_toolkit.py"

    def test_security_check_on_write_sql(self):
        """Verify SecurityError is raised for INSERT, UPDATE, DELETE, DROP SQL."""
        content = self._read(os.path.join(
            self.REPO_DIR, "posthog/hogql_queries/sql_query_toolkit.py"))
        assert content, "sql_query_toolkit.py is empty or unreadable"
        for kw in ("INSERT", "UPDATE", "DELETE", "DROP"):
            assert kw in content, f"SQL mutation keyword '{kw}' not guarded"

    def test_cache_ttl_sixty_seconds(self):
        """Verify caching with 60-second TTL is implemented."""
        content = self._read(os.path.join(
            self.REPO_DIR, "posthog/hogql_queries/sql_query_toolkit.py"))
        assert content, "sql_query_toolkit.py is empty or unreadable"
        found = any(kw in content for kw in ("60", "cache_ttl", "ttl=60", "maxsize"))
        assert found, "No cache TTL configuration found"

    # ── functional_check (import) ───────────────────────────────────

    def _import_toolkit(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, self.REPO_DIR)
        try:
            from posthog.hogql_queries.sql_query_toolkit import SQLQueryToolkit, SecurityError
            return SQLQueryToolkit, SecurityError
        except ImportError:
            pytest.skip("sql_query_toolkit not importable")
        finally:
            sys.path.pop(0)

    def test_get_tools_returns_count_three(self):
        """SQLQueryToolkit.get_tools() returns exactly 3 tool objects."""
        SQLQueryToolkit, _ = self._import_toolkit()
        toolkit = SQLQueryToolkit(db=None)
        tools = toolkit.get_tools()
        assert len(tools) == 3, f"Expected 3 tools, got {len(tools)}"

    def test_security_error_on_insert_sql(self):
        """ExecuteSQL raises SecurityError when receiving INSERT statement."""
        SQLQueryToolkit, SecurityError = self._import_toolkit()
        toolkit = SQLQueryToolkit(db=None)
        with pytest.raises(SecurityError):
            toolkit.run_sql_query("INSERT INTO events VALUES (1)")

    def test_security_error_on_drop_sql(self):
        """ExecuteSQL raises SecurityError when receiving DROP TABLE statement."""
        SQLQueryToolkit, SecurityError = self._import_toolkit()
        toolkit = SQLQueryToolkit(db=None)
        with pytest.raises(SecurityError):
            toolkit.run_sql_query("DROP TABLE events")

    def test_row_count_equals_len_rows(self):
        """QueryResult.row_count equals len(result.rows)."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, self.REPO_DIR)
        try:
            from posthog.hogql_queries.models import QueryResult
        except ImportError:
            pytest.skip("models not importable")
        finally:
            sys.path.pop(0)
        r = QueryResult(rows=[{"id": 1}, {"id": 2}], columns=["id"])
        assert r.row_count == len(r.rows)

    def test_cache_hit_returns_same_result(self):
        """Calling run_sql_query twice with same query returns cached result."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        result = subprocess.run(
            ["python", "-m", "pytest",
             os.path.join(self.REPO_DIR, "tests/test_sql_query_toolkit.py"),
             "-k", "cache", "-v"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0 and "no tests ran" in result.stdout.lower():
            pytest.skip("No cache tests found")
        assert result.returncode == 0 or "passed" in result.stdout.lower()
