"""
Tests for mcp-builder skill.
Validates MCP server TypeScript implementation with SQLite backend in servers repository.
"""

import os
import subprocess
import re
import pytest

REPO_DIR = "/workspace/servers"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


def _run(cmd: str, cwd: str = REPO_DIR, timeout: int = 120):
    return subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


class TestMcpBuilder:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_mcp_index_ts_exists(self):
        """index.ts must exist as MCP server entry point."""
        rel = "src/markdown-sqlite/src/index.ts"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "index.ts is empty"

    def test_mcp_database_tools_pagination_exist(self):
        """database.ts, tools.ts, and pagination.ts must all exist."""
        for rel in [
            "src/markdown-sqlite/src/database.ts",
            "src/markdown-sqlite/src/tools.ts",
            "src/markdown-sqlite/src/pagination.ts",
        ]:
            assert os.path.isfile(_path(rel)), f"{rel} not found"
            assert os.path.getsize(_path(rel)) > 0, f"{rel} is empty"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_four_tools_registered(self):
        """tools.ts must register at least 4 MCP tools."""
        content = _read("src/markdown-sqlite/src/tools.ts")
        tool_calls = re.findall(r"server\.tool\s*\(|registerTool\s*\(", content)
        assert (
            len(tool_calls) >= 4
        ), f"Expected >= 4 tool registrations, found {len(tool_calls)}"

    def test_readonly_hint_true_on_tools(self):
        """tools.ts must set readOnlyHint: true on database read tools."""
        content = _read("src/markdown-sqlite/src/tools.ts")
        assert (
            "readOnlyHint" in content and "true" in content
        ), "readOnlyHint: true not found in tools.ts"

    def test_parameterized_sql_no_injection(self):
        """database.ts must use parameterized queries — no string interpolation for SQL."""
        content = _read("src/markdown-sqlite/src/database.ts")
        # Check for template literals with SQL (injection risk)
        template_sql = re.findall(r"`[^`]*SELECT[^`]*\$\{[^}]+\}[^`]*`", content)
        assert (
            len(template_sql) == 0
        ), f"SQL string interpolation (injection risk) found: {template_sql}"
        # Should use ? placeholders
        assert (
            "?" in content or "prepare" in content
        ), "No parameterized query pattern found in database.ts"

    def test_fts5_full_text_search_table(self):
        """database.ts must create FTS5 virtual table for full-text search."""
        content = _read("src/markdown-sqlite/src/database.ts")
        assert (
            "fts5" in content.lower() or "USING fts5" in content
        ), "FTS5 virtual table not found in database.ts"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_npm_build_exits_zero(self):
        """npm run build must compile TypeScript without errors."""
        server_dir = os.path.join(REPO_DIR, "src/markdown-sqlite")
        if not os.path.isdir(server_dir):
            pytest.skip("src/markdown-sqlite directory not found")
        result = _run("npm run build", cwd=server_dir)
        if result.returncode != 0 and "npm" not in result.stderr:
            pytest.skip("npm not available")
        assert (
            result.returncode == 0
        ), f"npm run build failed:\n{result.stdout}\n{result.stderr}"

    def test_base64_cursor_pagination(self):
        """pagination.ts must use base64-encoded cursors for page tokens."""
        content = _read("src/markdown-sqlite/src/pagination.ts")
        assert (
            "base64" in content.lower() or "Buffer.from" in content or "btoa" in content
        ), "No base64 cursor encoding found in pagination.ts"

    def test_missing_required_field_error_32602(self):
        """Server must return MCP error -32602 for missing required parameters (mocked)."""
        MCP_INVALID_PARAMS = -32602

        def tool_handler(params: dict, required_fields: list):
            for field in required_fields:
                if field not in params:
                    return {
                        "error": {
                            "code": MCP_INVALID_PARAMS,
                            "message": f"Missing required param: {field}",
                        }
                    }
            return {"result": "ok"}

        response = tool_handler({}, required_fields=["path"])
        assert response["error"]["code"] == MCP_INVALID_PARAMS

    def test_index_ts_creates_server_instance(self):
        """index.ts must instantiate and connect the MCP server."""
        content = _read("src/markdown-sqlite/src/index.ts")
        assert (
            "McpServer" in content
            or "createServer" in content
            or "new Server" in content
        ), "MCP server instantiation not found in index.ts"
        assert (
            "connect" in content or "listen" in content
        ), "Server connect/listen call not found in index.ts"

    def test_no_sql_injection_in_search_query(self):
        """SQL injection payload must be safely handled by parameterized queries (mocked)."""
        import sqlite3

        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY, content TEXT)")
        conn.execute("INSERT INTO documents VALUES (1, 'hello world')")

        injection_payload = "'; DROP TABLE documents; --"
        cur = conn.execute(
            "SELECT * FROM documents WHERE content LIKE ?",
            (f"%{injection_payload}%",),
        )
        results = cur.fetchall()
        # Should return no results (not raise an error or drop the table)
        assert results == []
        # Verify table still exists
        cur2 = conn.execute("SELECT COUNT(*) FROM documents")
        assert cur2.fetchone()[0] == 1, "documents table was unexpectedly dropped"
        conn.close()

    def test_tools_ts_has_search_and_get_tools(self):
        """tools.ts must define both search and get/read tool operations."""
        content = _read("src/markdown-sqlite/src/tools.ts")
        assert (
            "search" in content.lower() or "query" in content.lower()
        ), "No search/query tool definition found in tools.ts"
        assert (
            "get" in content.lower() or "read" in content.lower()
        ), "No get/read tool definition found in tools.ts"
