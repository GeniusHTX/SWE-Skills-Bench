"""
Tests for the add-admin-api-endpoint skill.
Verifies that the Ghost Admin API bookmark endpoint implementation
is correctly structured, includes proper schema, routing, controller
exports, and E2E test coverage.
"""

import os
import subprocess
import sys

import pytest

REPO_DIR = "/workspace/Ghost"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    full = _path(rel)
    if not os.path.isfile(full):
        pytest.skip(f"File not found: {full}")
    with open(full, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _run(
    cmd: list, cwd: str = REPO_DIR, timeout: int = 120
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _node_available() -> bool:
    try:
        r = subprocess.run(["node", "--version"], capture_output=True, timeout=10)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ---------------------------------------------------------------------------
# File path checks
# ---------------------------------------------------------------------------


class TestAddAdminApiEndpoint:
    """Test suite for the Ghost Admin API bookmark endpoint skill."""

    def test_bookmarks_controller_file_exists(self):
        """Verify bookmarks endpoint handler file is created at the expected path."""
        target = _path("ghost/core/core/server/api/endpoints/bookmarks.js")
        assert os.path.isfile(target), f"Controller file not found: {target}"
        assert os.path.getsize(target) > 0, "bookmarks.js must be non-empty"

    def test_bookmark_model_and_test_files_exist(self):
        """Verify bookmark model and E2E test file are created."""
        model = _path("ghost/core/core/server/models/bookmark.js")
        e2e = _path("ghost/core/test/e2e-api/admin/bookmarks.test.js")
        assert os.path.isfile(model), f"Model file not found: {model}"
        assert os.path.isfile(e2e), f"E2E test file not found: {e2e}"

    def test_schema_contains_bookmarks_table(self):
        """Verify schema.js is modified to include bookmarks table definition."""
        content = _read("ghost/core/core/server/data/schema/schema.js")
        assert "bookmarks" in content, "schema.js must contain 'bookmarks' table entry"
        assert "user_id" in content, "schema.js must define 'user_id' column"
        assert "post_id" in content, "schema.js must define 'post_id' column"

    # -----------------------------------------------------------------------
    # Semantic checks
    # -----------------------------------------------------------------------

    def test_schema_bookmarks_table_has_unique_constraint(self):
        """Verify the bookmarks schema includes a unique constraint on (user_id, post_id)."""
        content = _read("ghost/core/core/server/data/schema/schema.js")
        lower = content.lower()
        has_unique = (
            "unique" in lower or "uniquecombination" in lower or "uniqueindex" in lower
        )
        assert (
            has_unique
        ), "schema.js must contain a unique constraint referencing user_id and post_id in the bookmarks table"

    def test_controller_exports_crud_actions(self):
        """Verify bookmarks controller exports browse, read, add, and destroy actions."""
        content = _read("ghost/core/core/server/api/endpoints/bookmarks.js")
        for action in ("browse", "read", "add", "destroy"):
            assert (
                action in content
            ), f"bookmarks.js must define/export '{action}' action"

    def test_routes_register_bookmark_endpoints(self):
        """Verify routes.js registers /bookmarks/ route and references the bookmarks controller."""
        content = _read("ghost/core/core/server/web/api/endpoints/admin/routes.js")
        assert "bookmarks" in content, "routes.js must register a 'bookmarks' route"

    def test_controller_has_jsdoc_comments(self):
        """Verify JSDoc comments are present on controller method exports."""
        content = _read("ghost/core/core/server/api/endpoints/bookmarks.js")
        assert (
            "/**" in content
        ), "bookmarks.js must contain JSDoc-style block comments ('/**')"

    # -----------------------------------------------------------------------
    # Functional checks (command)
    # -----------------------------------------------------------------------

    def test_schema_js_is_parseable_javascript(self):
        """Verify schema.js is syntactically valid JavaScript using node --check."""
        if not _node_available():
            pytest.skip("node not available in this environment")
        rel = "ghost/core/core/server/data/schema/schema.js"
        target = _path(rel)
        if not os.path.isfile(target):
            pytest.skip(f"File not found: {target}")
        result = _run(["node", "--check", target])
        assert (
            result.returncode == 0
        ), f"schema.js has syntax errors:\nstdout: {result.stdout}\nstderr: {result.stderr}"

    def test_bookmarks_controller_is_parseable_javascript(self):
        """Verify bookmarks.js controller is syntactically valid JavaScript."""
        if not _node_available():
            pytest.skip("node not available in this environment")
        rel = "ghost/core/core/server/api/endpoints/bookmarks.js"
        target = _path(rel)
        if not os.path.isfile(target):
            pytest.skip(f"File not found: {target}")
        result = _run(["node", "--check", target])
        assert (
            result.returncode == 0
        ), f"bookmarks.js has syntax errors:\nstdout: {result.stdout}\nstderr: {result.stderr}"

    def test_route_registration_syntax_check(self):
        """Verify routes.js is syntactically valid after modification."""
        if not _node_available():
            pytest.skip("node not available in this environment")
        rel = "ghost/core/core/server/web/api/endpoints/admin/routes.js"
        target = _path(rel)
        if not os.path.isfile(target):
            pytest.skip(f"File not found: {target}")
        result = _run(["node", "--check", target])
        assert (
            result.returncode == 0
        ), f"routes.js has syntax errors:\nstdout: {result.stdout}\nstderr: {result.stderr}"

    def test_note_field_length_in_schema(self):
        """Verify schema.js definition for note field specifies a max length."""
        content = _read("ghost/core/core/server/data/schema/schema.js")
        lower = content.lower()
        assert (
            "maxlength" in lower or "max_length" in lower or "varchar" in lower
        ), "The 'note' field in the bookmarks table must specify a max length constraint"

    def test_e2e_test_file_covers_duplicate_rejection(self):
        """Verify E2E test file includes test case for 422 on duplicate bookmark."""
        content = _read("ghost/core/test/e2e-api/admin/bookmarks.test.js")
        has_422 = "422" in content
        has_already_exists = "already exists" in content.lower()
        assert (
            has_422 or has_already_exists
        ), "E2E test file must include a test case for duplicate bookmark (422 or 'already exists')"

    def test_e2e_test_file_covers_authorization(self):
        """Verify E2E test file includes test case for 404 when accessing another user's bookmark."""
        content = _read("ghost/core/test/e2e-api/admin/bookmarks.test.js")
        assert (
            "404" in content
        ), "E2E test file must test that accessing another user's bookmark returns 404"
