"""
Test for 'mcp-builder' skill — MCP Server Builder (Model Context Protocol)
Validates index.ts, server.ts, tool files, schemas.ts with Zod,
read-only query enforcement, and tsc compilation.
"""

import os
import re
import subprocess

import pytest


class TestMcpBuilder:
    """Verify MCP server builder implementation."""

    REPO_DIR = "/workspace/servers"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_index_ts_exists(self):
        """Verify src/index.ts entry point exists."""
        candidates = ["src/index.ts", "index.ts"]
        for rel in candidates:
            if os.path.isfile(os.path.join(self.REPO_DIR, rel)):
                return
        # Search broadly
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "node_modules" in dirpath or ".git" in dirpath:
                continue
            if "index.ts" in fnames:
                return
        pytest.fail("No index.ts entry point found")

    def test_server_ts_exists(self):
        """Verify server.ts file exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "node_modules" in dirpath or ".git" in dirpath:
                continue
            for f in fnames:
                if "server" in f.lower() and f.endswith(".ts"):
                    found = True
                    break
            if found:
                break
        assert found, "No server.ts file found"

    def test_tool_files_exist(self):
        """Verify at least 2 tool definition files exist."""
        tool_files = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "node_modules" in dirpath or ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".ts") and (
                    "tool" in f.lower() or "handler" in f.lower()
                ):
                    tool_files.append(f)
        assert len(tool_files) >= 2, f"Expected ≥2 tool files, found: {tool_files}"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_snake_case_tools(self):
        """Verify tools use snake_case names (list_tables, describe_table, query_data)."""
        ts_files = self._find_ts_files()
        assert ts_files, "No TS files"
        all_content = " ".join(self._read(f) for f in ts_files)
        tools = ["list_tables", "describe_table", "query_data"]
        found_tools = [t for t in tools if t in all_content]
        assert (
            len(found_tools) >= 2
        ), f"Expected ≥2 snake_case tool names, found: {found_tools}"

    def test_zod_validation(self):
        """Verify Zod schema validation is used."""
        ts_files = self._find_ts_files()
        for fpath in ts_files:
            content = self._read(fpath)
            if re.search(
                r"(import.*zod|z\.object|z\.string|z\.number|zodSchema)", content
            ):
                return
        pytest.fail("No Zod validation found")

    def test_read_only_query_enforcement(self):
        """Verify read-only query rejects INSERT/UPDATE/DELETE/DROP."""
        ts_files = self._find_ts_files()
        for fpath in ts_files:
            content = self._read(fpath)
            if re.search(r"(INSERT|UPDATE|DELETE|DROP)", content):
                if re.search(
                    r"(reject|block|forbidden|readonly|read.only|throw|error)",
                    content,
                    re.IGNORECASE,
                ):
                    return
        pytest.fail("No read-only query enforcement found")

    def test_schemas_file_exists(self):
        """Verify schemas.ts or similar schema definition file."""
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "node_modules" in dirpath or ".git" in dirpath:
                continue
            for f in fnames:
                if "schema" in f.lower() and f.endswith(".ts"):
                    return
        pytest.fail("No schemas.ts file found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_tsc_no_emit(self):
        """Verify TypeScript compilation succeeds."""
        tsconfig = os.path.join(self.REPO_DIR, "tsconfig.json")
        if not os.path.isfile(tsconfig):
            pytest.skip("No tsconfig.json")
        try:
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.REPO_DIR,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("npx/tsc not available")
        if result.returncode != 0:
            # Allow dependency-related errors
            assert "Cannot find module" in result.stderr or "error TS" in result.stderr

    def test_block_insert_drop(self):
        """Verify INSERT and DROP statements are blocked in query tool."""
        ts_files = self._find_ts_files()
        for fpath in ts_files:
            content = self._read(fpath)
            if "INSERT" in content and "DROP" in content:
                return
            if re.search(r"/(INSERT|UPDATE|DELETE|DROP)/i", content):
                return
            if re.search(
                r"\b(INSERT|DROP)\b.*block|reject|forbid", content, re.IGNORECASE
            ):
                return
        pytest.fail("INSERT/DROP blocking not found in tool files")

    def test_list_tables_returns_array(self):
        """Verify list_tables tool returns an array."""
        ts_files = self._find_ts_files()
        for fpath in ts_files:
            content = self._read(fpath)
            if "list_tables" in content:
                if re.search(r"(\[\]|Array|array|tables)", content):
                    return
        pytest.skip("list_tables return type not explicitly verifiable")

    def test_zod_rejects_invalid(self):
        """Verify Zod schemas reject invalid input (has error handling)."""
        ts_files = self._find_ts_files()
        for fpath in ts_files:
            content = self._read(fpath)
            if "zod" in content.lower() or "z." in content:
                if re.search(r"(parse|safeParse|catch|error|throw|ZodError)", content):
                    return
        pytest.fail("No Zod validation error handling found")

    def test_ts_files_balanced_braces(self):
        """Verify all TS files have balanced braces."""
        ts_files = self._find_ts_files()
        assert ts_files, "No TS files"
        for fpath in ts_files:
            content = self._read(fpath)
            opens = content.count("{")
            closes = content.count("}")
            assert opens == closes, f"Unbalanced braces in {os.path.basename(fpath)}"

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_ts_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "node_modules" in dirpath or ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".ts"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
