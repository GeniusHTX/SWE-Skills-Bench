"""
Test for 'mcp-builder' skill — MCP Server for Markdown Knowledge Base
Validates that the Agent created an MCP server under src/markdown-sqlite/
with tool definitions, SQLite integration, and build configuration.
"""

import os
import re
import subprocess
import json

import pytest


class TestMcpBuilder:
    """Verify MCP Markdown-SQLite server."""

    REPO_DIR = "/workspace/servers"
    SERVER_DIR = "src/markdown-sqlite"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: Directory and package.json
    # ------------------------------------------------------------------

    def test_server_directory_exists(self):
        """src/markdown-sqlite/ must exist."""
        assert os.path.isdir(os.path.join(self.REPO_DIR, self.SERVER_DIR))

    def test_package_json_exists(self):
        """package.json must exist in the server directory."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.SERVER_DIR, "package.json")
        )

    def test_package_json_valid(self):
        """package.json must be valid JSON."""
        content = self._read(self.SERVER_DIR, "package.json")
        data = json.loads(content)
        assert "name" in data, "package.json missing name"

    def test_package_has_build_script(self):
        """package.json must have a build script."""
        content = self._read(self.SERVER_DIR, "package.json")
        data = json.loads(content)
        scripts = data.get("scripts", {})
        assert "build" in scripts, "package.json missing build script"

    # ------------------------------------------------------------------
    # L1: TypeScript source files
    # ------------------------------------------------------------------

    def test_has_typescript_source(self):
        """Server must have TypeScript source files."""
        server_dir = os.path.join(self.REPO_DIR, self.SERVER_DIR)
        ts_files = []
        for root, _dirs, files in os.walk(server_dir):
            for f in files:
                if f.endswith(".ts") and not f.endswith(".d.ts"):
                    ts_files.append(f)
        assert len(ts_files) >= 1, "No TypeScript source files found"

    # ------------------------------------------------------------------
    # L2: MCP tools — at least 3
    # ------------------------------------------------------------------

    def test_defines_index_tool(self):
        """Server must define an indexing tool."""
        server_dir = os.path.join(self.REPO_DIR, self.SERVER_DIR)
        found = False
        for root, _dirs, files in os.walk(server_dir):
            for f in files:
                if f.endswith(".ts"):
                    with open(os.path.join(root, f), "r", errors="ignore") as fh:
                        text = fh.read()
                    if re.search(r"index|Index", text):
                        found = True
                        break
        assert found, "No indexing tool found"

    def test_defines_search_tool(self):
        """Server must define a search tool."""
        server_dir = os.path.join(self.REPO_DIR, self.SERVER_DIR)
        found = False
        for root, _dirs, files in os.walk(server_dir):
            for f in files:
                if f.endswith(".ts"):
                    with open(os.path.join(root, f), "r", errors="ignore") as fh:
                        text = fh.read()
                    if re.search(r"search|Search|query|Query", text):
                        found = True
                        break
        assert found, "No search tool found"

    def test_defines_retrieve_tool(self):
        """Server must define a retrieval tool."""
        server_dir = os.path.join(self.REPO_DIR, self.SERVER_DIR)
        found = False
        for root, _dirs, files in os.walk(server_dir):
            for f in files:
                if f.endswith(".ts"):
                    with open(os.path.join(root, f), "r", errors="ignore") as fh:
                        text = fh.read()
                    if re.search(r"retrieve|Retrieve|get.*doc|getDocument", text):
                        found = True
                        break
        assert found, "No retrieval tool found"

    def test_registers_at_least_three_tools(self):
        """Server must register at least 3 MCP tools."""
        server_dir = os.path.join(self.REPO_DIR, self.SERVER_DIR)
        tool_count = 0
        for root, _dirs, files in os.walk(server_dir):
            for f in files:
                if f.endswith(".ts"):
                    with open(os.path.join(root, f), "r", errors="ignore") as fh:
                        text = fh.read()
                    tool_count += len(
                        re.findall(r"tool\(|addTool|registerTool|name:\s*['\"]", text)
                    )
        assert (
            tool_count >= 3
        ), f"Only {tool_count} tool registration(s) — need at least 3"

    # ------------------------------------------------------------------
    # L2: SQLite integration
    # ------------------------------------------------------------------

    def test_uses_sqlite(self):
        """Server must use SQLite for storage."""
        server_dir = os.path.join(self.REPO_DIR, self.SERVER_DIR)
        found = False
        for root, _dirs, files in os.walk(server_dir):
            for f in files:
                if f.endswith((".ts", ".json")):
                    with open(os.path.join(root, f), "r", errors="ignore") as fh:
                        text = fh.read()
                    if re.search(r"sqlite|better-sqlite3|sql\.js", text, re.IGNORECASE):
                        found = True
                        break
        assert found, "No SQLite usage found"

    def test_uses_full_text_search(self):
        """Server must enable FTS on stored content."""
        server_dir = os.path.join(self.REPO_DIR, self.SERVER_DIR)
        found = False
        for root, _dirs, files in os.walk(server_dir):
            for f in files:
                if f.endswith(".ts"):
                    with open(os.path.join(root, f), "r", errors="ignore") as fh:
                        text = fh.read()
                    if re.search(r"fts|FTS|full.text|MATCH", text, re.IGNORECASE):
                        found = True
                        break
        assert found, "No full-text search usage found"

    def test_tracks_metadata(self):
        """Indexed documents must track metadata (path, title, timestamp)."""
        server_dir = os.path.join(self.REPO_DIR, self.SERVER_DIR)
        metadata_fields = set()
        for root, _dirs, files in os.walk(server_dir):
            for f in files:
                if f.endswith(".ts"):
                    with open(os.path.join(root, f), "r", errors="ignore") as fh:
                        text = fh.read()
                    for field in ["path", "title", "timestamp", "indexed_at"]:
                        if field in text.lower():
                            metadata_fields.add(field)
        assert (
            len(metadata_fields) >= 2
        ), f"Only {len(metadata_fields)} metadata field(s): {metadata_fields}"
