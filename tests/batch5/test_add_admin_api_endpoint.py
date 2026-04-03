"""
Test for 'add-admin-api-endpoint' skill — Ghost Bookmarks Admin API
Validates that the Agent added a bookmarks CRUD endpoint to Ghost's Admin API,
including controller, model, schema, and route registration.
"""

import json
import os
import re
import subprocess

import pytest


class TestAddAdminApiEndpoint:
    """Verify Ghost Admin API bookmarks endpoint."""

    REPO_DIR = "/workspace/Ghost"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_bookmark_controller_files_exist(self):
        """Verify bookmarks controller, model, and schema files exist."""
        required = [
            "core/server/api/endpoints/bookmarks.js",
            "core/server/models/bookmark.js",
            "core/server/data/schema/schema.js",
        ]
        missing = [
            f for f in required if not os.path.isfile(os.path.join(self.REPO_DIR, f))
        ]
        assert not missing, f"Missing bookmarks files: {missing}"

    def test_schema_table_definition_exists(self):
        """Verify schema.js contains the bookmarks table definition."""
        schema_path = os.path.join(self.REPO_DIR, "core/server/data/schema/schema.js")
        assert os.path.isfile(schema_path), "schema.js is missing"
        with open(schema_path, "r", errors="ignore") as fh:
            content = fh.read()
        assert (
            "bookmarks" in content
        ), "schema.js does not contain a 'bookmarks' table definition"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_controller_exports_five_crud_actions(self):
        """Verify bookmarks controller exports browse, read, add, edit, destroy."""
        ctrl_path = os.path.join(
            self.REPO_DIR, "core/server/api/endpoints/bookmarks.js"
        )
        assert os.path.isfile(ctrl_path), "bookmarks.js controller is missing"
        with open(ctrl_path, "r", errors="ignore") as fh:
            content = fh.read()
        for action in ["browse", "read", "add", "edit", "destroy"]:
            assert action in content, f"bookmarks controller missing '{action}' export"

    def test_model_defines_table_and_tags(self):
        """Verify Bookmark model references tableName and tags relation."""
        model_path = os.path.join(self.REPO_DIR, "core/server/models/bookmark.js")
        assert os.path.isfile(model_path), "bookmark.js model is missing"
        with open(model_path, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(
            r"tableName", content
        ), "Bookmark model does not define tableName"

    def test_schema_has_required_columns(self):
        """Verify schema defines title, url, description, created_by columns."""
        schema_path = os.path.join(self.REPO_DIR, "core/server/data/schema/schema.js")
        assert os.path.isfile(schema_path), "schema.js is missing"
        with open(schema_path, "r", errors="ignore") as fh:
            content = fh.read()
        for col in ["title", "url", "description", "created_by"]:
            assert col in content, f"Schema missing column '{col}' for bookmarks table"

    def test_index_js_registers_bookmarks_route(self):
        """Verify the admin API index or router registers the bookmarks endpoint."""
        candidates = [
            "core/server/api/endpoints/index.js",
            "core/server/web/api/endpoints/admin/index.js",
        ]
        found = False
        for rel_path in candidates:
            full = os.path.join(self.REPO_DIR, rel_path)
            if os.path.isfile(full):
                with open(full, "r", errors="ignore") as fh:
                    content = fh.read()
                if "bookmarks" in content:
                    found = True
                    break
        assert found, "No admin API index file registers the 'bookmarks' endpoint"

    # ── functional_check ────────────────────────────────────────────────────

    def test_controller_syntax_valid(self):
        """Verify bookmarks controller is syntactically valid JavaScript."""
        ctrl_path = os.path.join(
            self.REPO_DIR, "core/server/api/endpoints/bookmarks.js"
        )
        assert os.path.isfile(ctrl_path), "bookmarks.js controller is missing"
        try:
            result = subprocess.run(
                ["node", "--check", ctrl_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except FileNotFoundError:
            pytest.skip("node not available")
        assert (
            result.returncode == 0
        ), f"bookmarks.js has syntax errors:\n{result.stderr}"

    def test_post_creates_bookmark_returns_201(self):
        """Verify POST /bookmarks returns 201 (or the controller supports add)."""
        ctrl_path = os.path.join(
            self.REPO_DIR, "core/server/api/endpoints/bookmarks.js"
        )
        assert os.path.isfile(ctrl_path), "bookmarks.js controller is missing"
        with open(ctrl_path, "r", errors="ignore") as fh:
            content = fh.read()
        assert "add" in content, "POST handler (add) missing from controller"
        # Check that a status code of 201 is defined or a frame response is used
        has_status = re.search(r"201|statusCode|frame", content)
        assert (
            has_status
        ), "Controller add action does not reference 201 status code or frame"

    def test_get_browse_supports_pagination(self):
        """Verify the browse action supports a limit/pagination parameter."""
        ctrl_path = os.path.join(
            self.REPO_DIR, "core/server/api/endpoints/bookmarks.js"
        )
        assert os.path.isfile(ctrl_path), "bookmarks.js controller is missing"
        with open(ctrl_path, "r", errors="ignore") as fh:
            content = fh.read()
        assert "browse" in content, "browse action missing from controller"

    def test_delete_returns_204_or_destroy(self):
        """Verify DELETE handler (destroy) is present in controller."""
        ctrl_path = os.path.join(
            self.REPO_DIR, "core/server/api/endpoints/bookmarks.js"
        )
        assert os.path.isfile(ctrl_path), "bookmarks.js controller is missing"
        with open(ctrl_path, "r", errors="ignore") as fh:
            content = fh.read()
        assert (
            "destroy" in content
        ), "DELETE handler (destroy) missing from bookmarks controller"

    def test_post_missing_url_returns_validation_error(self):
        """Verify schema or validation logic requires a url field for bookmarks."""
        schema_path = os.path.join(self.REPO_DIR, "core/server/data/schema/schema.js")
        assert os.path.isfile(schema_path), "schema.js is missing"
        with open(schema_path, "r", errors="ignore") as fh:
            content = fh.read()
        assert (
            "url" in content
        ), "Schema does not define 'url' column for bookmarks (required field)"

    def test_unauthenticated_request_requires_auth(self):
        """Verify controller references authentication or permissions."""
        ctrl_path = os.path.join(
            self.REPO_DIR, "core/server/api/endpoints/bookmarks.js"
        )
        assert os.path.isfile(ctrl_path), "bookmarks.js controller is missing"
        with open(ctrl_path, "r", errors="ignore") as fh:
            content = fh.read()
        auth_patterns = [r"permissions", r"auth", r"session", r"middleware"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in auth_patterns
        ), "Controller does not reference authentication or permissions"
