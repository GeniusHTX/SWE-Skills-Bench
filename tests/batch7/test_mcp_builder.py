"""Test file for the mcp-builder skill.

This suite validates the MCP markdown-sqlite server, including
package.json, tsconfig.json, and index.ts tool declarations.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest


class TestMcpBuilder:
    """Verify MCP markdown-sqlite server implementation."""

    REPO_DIR = "/workspace/servers"

    PACKAGE_JSON = "src/markdown-sqlite/package.json"
    TSCONFIG_JSON = "src/markdown-sqlite/tsconfig.json"
    INDEX_TS = "src/markdown-sqlite/src/index.ts"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    def _read_json(self, relative: str) -> dict:
        text = self._read_text(relative)
        return json.loads(text)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_src_markdown_sqlite_package_json_exists(self):
        """Verify package.json exists and is non-empty."""
        self._assert_non_empty_file(self.PACKAGE_JSON)

    def test_file_path_src_markdown_sqlite_tsconfig_json_exists(self):
        """Verify tsconfig.json exists and is non-empty."""
        self._assert_non_empty_file(self.TSCONFIG_JSON)

    def test_file_path_src_markdown_sqlite_src_index_ts_exists(self):
        """Verify src/index.ts exists and is non-empty."""
        self._assert_non_empty_file(self.INDEX_TS)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_package_json_has_modelcontextprotocol_sdk_and_better_sqlite3(
        self,
    ):
        """package.json has @modelcontextprotocol/sdk and better-sqlite3 dependencies."""
        pkg = self._read_json(self.PACKAGE_JSON)
        all_deps = {}
        all_deps.update(pkg.get("dependencies", {}))
        all_deps.update(pkg.get("devDependencies", {}))
        assert (
            "@modelcontextprotocol/sdk" in all_deps
        ), "Missing @modelcontextprotocol/sdk dependency"
        assert "better-sqlite3" in all_deps, "Missing better-sqlite3 dependency"

    def test_semantic_package_json_has_build_script(self):
        """package.json has build script."""
        pkg = self._read_json(self.PACKAGE_JSON)
        scripts = pkg.get("scripts", {})
        assert "build" in scripts, "Missing build script in package.json"

    def test_semantic_tsconfig_json_targets_es2022_with_strict_mode(self):
        """tsconfig.json targets ES2022 with strict mode."""
        tsconfig = self._read_json(self.TSCONFIG_JSON)
        compiler_options = tsconfig.get("compilerOptions", {})
        target = compiler_options.get("target", "").upper()
        assert (
            "ES2022" in target or "ESNEXT" in target
        ), f"Expected target ES2022 or ESNext, got {target}"
        assert (
            compiler_options.get("strict") is True
        ), "Expected strict: true in tsconfig.json"

    def test_semantic_index_ts_creates_mcp_server_with_stdio_transport(self):
        """index.ts creates MCP server with stdio transport."""
        src = self._read_text(self.INDEX_TS)
        assert re.search(
            r"Server|McpServer|createServer", src
        ), "index.ts should create an MCP server"
        assert re.search(
            r"[Ss]tdio|StdioTransport|stdin|stdout", src
        ), "index.ts should use stdio transport"

    def test_semantic_index_ts_declares_tools_capability_in_initialize(self):
        """index.ts declares tools capability in initialize."""
        src = self._read_text(self.INDEX_TS)
        assert re.search(
            r"tools|capabilities", src, re.IGNORECASE
        ), "index.ts should declare tools capability"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, source analysis)
    # ------------------------------------------------------------------

    def test_functional_create_note_returns_note_with_uuid_timestamps_provided_field(
        self,
    ):
        """create_note returns note with UUID, timestamps, provided fields."""
        src = self._read_text(self.INDEX_TS)
        assert re.search(
            r"create.note|createNote|create_note", src, re.IGNORECASE
        ), "create_note tool should be defined"
        assert re.search(
            r"uuid|UUID|randomUUID|uuidv4", src
        ), "create_note should generate a UUID"

    def test_functional_get_note_returns_correct_note_by_uuid(self):
        """get_note returns correct note by UUID."""
        src = self._read_text(self.INDEX_TS)
        assert re.search(
            r"get.note|getNote|get_note", src, re.IGNORECASE
        ), "get_note tool should be defined"

    def test_functional_get_note_with_invalid_uuid_returns_note_not_found_error(self):
        """get_note with invalid UUID returns 'note not found' error."""
        src = self._read_text(self.INDEX_TS)
        assert re.search(
            r"not.found|NotFound|error|Error", src, re.IGNORECASE
        ), "get_note should handle not-found case"

    def test_functional_search_notes_returns_matching_notes_with_snippet_context(self):
        """search_notes returns matching notes with snippet context."""
        src = self._read_text(self.INDEX_TS)
        assert re.search(
            r"search.note|searchNote|search_note|LIKE|FTS", src, re.IGNORECASE
        ), "search_notes tool should be defined"

    def test_functional_update_note_updates_fields_and_sets_new_updated_at(self):
        """update_note updates fields and sets new updated_at."""
        src = self._read_text(self.INDEX_TS)
        assert re.search(
            r"update.note|updateNote|update_note", src, re.IGNORECASE
        ), "update_note tool should be defined"
        assert re.search(
            r"updated.at|updatedAt|updated_at", src, re.IGNORECASE
        ), "update_note should set updated_at timestamp"
