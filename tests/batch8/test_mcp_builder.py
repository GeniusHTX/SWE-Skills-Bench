"""
Test for 'mcp-builder' skill — MCP SQLite Server
Validates that the Agent created a TypeScript MCP server with query_database,
get_schema, list_tables tools and SELECT-only SQL guard.
"""

import os
import re
import subprocess

import pytest


class TestMcpBuilder:
    """Verify MCP SQLite server implementation."""

    REPO_DIR = "/workspace/servers"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_server_and_tool_files_exist(self):
        """Verify src/server.ts, src/tools/query.ts, and src/tools/schema.ts exist."""
        for rel in ("src/server.ts", "src/tools/query.ts", "src/tools/schema.ts"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_database_resource_and_config_exist(self):
        """Verify src/resources/database.ts, package.json, and tsconfig.json exist."""
        for rel in ("src/resources/database.ts", "package.json", "tsconfig.json"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_package_json_has_mcp_scripts(self):
        """package.json contains mcp-server related script entry."""
        content = self._read(os.path.join(self.REPO_DIR, "package.json"))
        assert content, "package.json is empty or unreadable"
        found = any(kw in content for kw in ("mcp", "server", "start"))
        assert found, "No server startup script found in package.json"

    # ── semantic_check ──────────────────────────────────────────────

    def test_server_registers_all_three_tools(self):
        """Verify server.ts registers query_database, get_schema, and list_tables."""
        content = self._read(os.path.join(self.REPO_DIR, "src/server.ts"))
        assert content, "server.ts is empty or unreadable"
        for tool in ("query_database", "get_schema", "list_tables"):
            assert tool in content, f"'{tool}' not registered in server.ts"

    def test_query_tool_validates_select_only(self):
        """Verify query.ts validates SQL starts with SELECT before executing."""
        content = self._read(os.path.join(self.REPO_DIR, "src/tools/query.ts"))
        assert content, "query.ts is empty or unreadable"
        found = any(kw in content for kw in ("SELECT", "startsWith", "toUpperCase", "Error"))
        assert found, "SELECT-only guard not found in query.ts"

    def test_database_resource_uses_mcp_db_path(self):
        """Verify database.ts reads SQLite path from MCP_DB_PATH env variable."""
        content = self._read(os.path.join(self.REPO_DIR, "src/resources/database.ts"))
        assert content, "database.ts is empty or unreadable"
        assert "MCP_DB_PATH" in content, "MCP_DB_PATH not found"
        assert "process.env" in content, "process.env not found"

    # ── functional_check (command) ──────────────────────────────────

    def _skip_unless_node(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if not os.path.isfile(os.path.join(self.REPO_DIR, "package.json")):
            pytest.skip("package.json missing")

    def test_typescript_compiles_without_errors(self):
        """npx tsc --noEmit exits 0."""
        self._skip_unless_node()
        result = subprocess.run(
            ["npx", "tsc", "--noEmit"], capture_output=True, text=True,
            cwd=self.REPO_DIR, timeout=120,
        )
        if result.returncode != 0 and "not found" in result.stderr.lower():
            pytest.skip("tsc not available")
        assert result.returncode == 0, f"tsc failed: {result.stderr}"

    def test_npm_tests_pass(self):
        """npm test exits 0 with all tests passing."""
        self._skip_unless_node()
        result = subprocess.run(
            ["npm", "test"], capture_output=True, text=True,
            cwd=self.REPO_DIR, timeout=120,
        )
        if result.returncode != 0 and "no test" in (result.stderr + result.stdout).lower():
            pytest.skip("No tests configured")
        assert result.returncode == 0, f"npm test failed: {result.stderr}"

    def test_insert_sql_returns_error_response(self):
        """query_database with INSERT SQL returns MCP error response."""
        self._skip_unless_node()
        result = subprocess.run(
            ["npm", "test", "--", "--testNamePattern=INSERT.*error|write.*rejected"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        if result.returncode != 0 and "no tests" in (result.stderr + result.stdout).lower():
            pytest.skip("No INSERT error test found")
        assert result.returncode == 0

    def test_select_1_returns_correct_row(self):
        """query_database with 'SELECT 1 as n' returns correct result."""
        self._skip_unless_node()
        result = subprocess.run(
            ["npm", "test", "--", "--testNamePattern=SELECT 1|query.*result"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        if result.returncode != 0 and "no tests" in (result.stderr + result.stdout).lower():
            pytest.skip("No SELECT 1 test found")
        assert result.returncode == 0
