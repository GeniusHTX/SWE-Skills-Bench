"""
Test for 'mcp-builder' skill — Markdown-SQLite MCP Server
Validates that the Agent created a functional MCP server with markdown ingestion,
SQLite storage, Zod validation, and proper TypeScript project structure.
"""

import json
import os

import pytest


class TestMcpBuilder:
    """Verify Markdown-SQLite MCP server implementation."""

    REPO_DIR = "/workspace/servers"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    # ---- file_path_check ----

    def test_src_markdown_sqlite_exists(self):
        """Verifies src/markdown-sqlite directory exists."""
        path = os.path.join(self.REPO_DIR, "src/markdown-sqlite")
        assert os.path.exists(path), f"Expected path not found: {path}"

    def test_package_json_exists(self):
        """Verifies package.json exists."""
        path = os.path.join(self.REPO_DIR, "package.json")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_tsconfig_json_exists(self):
        """Verifies tsconfig.json exists."""
        path = os.path.join(self.REPO_DIR, "tsconfig.json")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_src_index_ts_exists(self):
        """Verifies src/index.ts exists."""
        path = os.path.join(self.REPO_DIR, "src/index.ts")
        assert os.path.exists(path), f"Expected file not found: {path}"

    # ---- semantic_check ----

    def test_sem_db_ts_readable(self):
        """Reads db.ts from markdown-sqlite src directory."""
        md_sqlite = os.path.join(self.REPO_DIR, "src/markdown-sqlite")
        db_text = open(os.path.join(md_sqlite, "src/db.ts")).read()
        assert len(db_text) > 0, "db.ts is empty"

    def test_sem_db_schema_tables(self):
        """Verifies CREATE TABLE with documents and sections tables."""
        md_sqlite = os.path.join(self.REPO_DIR, "src/markdown-sqlite")
        db_text = open(os.path.join(md_sqlite, "src/db.ts")).read()
        assert (
            "CREATE TABLE" in db_text
            and "documents" in db_text
            and "sections" in db_text
        ), "DB schema missing"

    def test_sem_sections_fk(self):
        """Verifies sections FK to documents."""
        md_sqlite = os.path.join(self.REPO_DIR, "src/markdown-sqlite")
        db_text = open(os.path.join(md_sqlite, "src/db.ts")).read()
        assert "document_id" in db_text, "sections FK to documents missing"

    def test_sem_ingest_ts_readable(self):
        """Reads ingest.ts (edge case)."""
        md_sqlite = os.path.join(self.REPO_DIR, "src/markdown-sqlite")
        ingest_text = open(os.path.join(md_sqlite, "src/tools/ingest.ts")).read()
        assert len(ingest_text) > 0, "ingest.ts is empty"

    def test_sem_zod_validation_in_ingest(self):
        """Verifies Zod validation in ingest.ts."""
        md_sqlite = os.path.join(self.REPO_DIR, "src/markdown-sqlite")
        ingest_text = open(os.path.join(md_sqlite, "src/tools/ingest.ts")).read()
        assert (
            "z." in ingest_text or "zod" in ingest_text.lower()
        ), "Zod validation missing in ingest.ts"

    def test_sem_markdown_heading_parsing(self):
        """Verifies markdown heading parsing in ingest.ts."""
        md_sqlite = os.path.join(self.REPO_DIR, "src/markdown-sqlite")
        ingest_text = open(os.path.join(md_sqlite, "src/tools/ingest.ts")).read()
        assert (
            "## " in ingest_text or "heading" in ingest_text or "split" in ingest_text
        ), "Markdown heading parsing not found"

    # ---- functional_check ----

    def test_func_package_json_readable(self):
        """Reads package.json from markdown-sqlite."""
        md_sqlite = os.path.join(self.REPO_DIR, "src/markdown-sqlite")
        pkg = open(os.path.join(md_sqlite, "package.json")).read()
        assert len(pkg) > 0, "package.json is empty"

    def test_func_package_json_valid(self):
        """Verifies package.json is valid JSON."""
        md_sqlite = os.path.join(self.REPO_DIR, "src/markdown-sqlite")
        pkg = open(os.path.join(md_sqlite, "package.json")).read()
        pkg_json = json.loads(pkg)
        assert isinstance(pkg_json, dict), "package.json is not a valid JSON object"

    def test_func_package_json_bin_field(self):
        """Verifies bin field in package.json."""
        md_sqlite = os.path.join(self.REPO_DIR, "src/markdown-sqlite")
        pkg = open(os.path.join(md_sqlite, "package.json")).read()
        pkg_json = json.loads(pkg)
        assert "bin" in pkg_json, "bin field missing from package.json"

    def test_func_package_json_build_script(self):
        """Verifies build script in package.json."""
        md_sqlite = os.path.join(self.REPO_DIR, "src/markdown-sqlite")
        pkg = open(os.path.join(md_sqlite, "package.json")).read()
        pkg_json = json.loads(pkg)
        assert "build" in pkg_json.get(
            "scripts", {}
        ), "build script missing from package.json"

    def test_func_better_sqlite3_dependency(self):
        """Verifies better-sqlite3 dependency."""
        md_sqlite = os.path.join(self.REPO_DIR, "src/markdown-sqlite")
        pkg = open(os.path.join(md_sqlite, "package.json")).read()
        pkg_json = json.loads(pkg)
        assert "better-sqlite3" in pkg_json.get(
            "dependencies", {}
        ) or "better-sqlite3" in str(pkg_json), "better-sqlite3 dependency missing"

    def test_func_zod_dependency(self):
        """Verifies zod dependency."""
        md_sqlite = os.path.join(self.REPO_DIR, "src/markdown-sqlite")
        pkg = open(os.path.join(md_sqlite, "package.json")).read()
        pkg_json = json.loads(pkg)
        assert "zod" in pkg_json.get("dependencies", {}) or "zod" in str(
            pkg_json
        ), "zod dependency missing"

    def test_func_list_ts_readable(self):
        """Reads list.ts tool file."""
        md_sqlite = os.path.join(self.REPO_DIR, "src/markdown-sqlite")
        list_text = open(os.path.join(md_sqlite, "src/tools/list.ts")).read()
        assert len(list_text) > 0, "list.ts is empty"

    def test_func_tag_filter_in_list(self):
        """Verifies tag filter parameter in list.ts."""
        md_sqlite = os.path.join(self.REPO_DIR, "src/markdown-sqlite")
        list_text = open(os.path.join(md_sqlite, "src/tools/list.ts")).read()
        assert "tag" in list_text, "tag filter parameter missing in list.ts"

    def test_func_failure_missing_filepath_zod_error(self):
        """Failure case: Zod validation should handle missing filePath."""
        md_sqlite = os.path.join(self.REPO_DIR, "src/markdown-sqlite")
        ingest_text = open(os.path.join(md_sqlite, "src/tools/ingest.ts")).read()
        assert (
            "z." in ingest_text or "zod" in ingest_text.lower()
        ), "Zod validation missing — cannot validate filePath requirement"
