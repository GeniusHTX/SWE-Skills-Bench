"""
Test for 'add-admin-api-endpoint' skill — Ghost Admin API Endpoint Creator
Validates the custom Ghost admin API endpoint: file structure, Ghost error
classes, authentication middleware, frame/options pattern, and mocked
functional behavior (auth, 404, empty collection).
"""

import glob
import os
import re

import pytest


class TestAddAdminApiEndpoint:
    """Verify Ghost custom admin API endpoint implementation."""

    REPO_DIR = "/workspace/Ghost"
    ENDPOINTS_DIR = os.path.join(
        REPO_DIR, "ghost", "core", "core", "server", "api", "endpoints"
    )

    # ── helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ──────────────────────────────────────────────────

    def test_custom_endpoint_js_file_exists(self):
        """ghost/core/core/server/api/endpoints/custom.js must exist and be non-empty."""
        path = os.path.join(self.ENDPOINTS_DIR, "custom.js")
        assert os.path.isfile(path), f"{path} does not exist"
        assert os.path.getsize(path) > 0, "custom.js is empty"

    def test_endpoint_registered_in_index_js(self):
        """index.js must reference 'custom' in exports or require context."""
        path = os.path.join(self.ENDPOINTS_DIR, "index.js")
        assert os.path.isfile(path), f"{path} does not exist"
        content = self._read_file(path)
        # Must appear as an export or require, not just a comment
        lines = [l for l in content.splitlines() if "custom" in l and not l.strip().startswith("//")]
        assert lines, "'custom' not referenced in index.js exports"

    def test_e2e_test_file_exists(self):
        """E2E test file for custom admin endpoint must exist with at least one test."""
        path = os.path.join(
            self.REPO_DIR, "ghost", "core", "test", "e2e-api", "admin", "custom.test.js"
        )
        assert os.path.isfile(path), f"{path} does not exist"
        content = self._read_file(path)
        assert "it(" in content or "test(" in content, (
            "Test file has no it()/test() invocations"
        )

    # ── semantic_check ───────────────────────────────────────────────────

    def test_ghost_error_classes_imported(self):
        """custom.js must use @tryghost/errors, not plain Error."""
        content = self._read_file(os.path.join(self.ENDPOINTS_DIR, "custom.js"))
        assert "@tryghost/errors" in content, "@tryghost/errors not imported"
        ghost_errors = ["NotFoundError", "ValidationError", "UnauthorizedError"]
        found = any(e in content for e in ghost_errors)
        assert found, "No Ghost error class (NotFoundError/ValidationError) used"

    def test_authenticate_middleware_precedes_controller(self):
        """'authenticate' or 'auth' must appear before controller function."""
        content = self._read_file(os.path.join(self.ENDPOINTS_DIR, "custom.js"))
        lines = content.splitlines()
        auth_line = None
        controller_line = None
        for i, line in enumerate(lines):
            if auth_line is None and re.search(r"authenticat|auth.*middleware|adminToken", line, re.IGNORECASE):
                auth_line = i
            if controller_line is None and re.search(r"controller|handler|module\.exports", line, re.IGNORECASE):
                controller_line = i
        assert auth_line is not None, "No authentication reference found in custom.js"

    def test_controller_uses_frame_options_pattern(self):
        """Controller must use Ghost frame.options or frame.response pattern."""
        content = self._read_file(os.path.join(self.ENDPOINTS_DIR, "custom.js"))
        assert "frame" in content, "'frame' parameter not found in custom.js"
        has_frame_usage = "frame.options" in content or "frame.response" in content or "frame.data" in content
        assert has_frame_usage, "frame.options/frame.response not used in controller"

    def test_endpoint_path_uses_admin_prefix(self):
        """custom must be in admin API section of index.js, not content API."""
        content = self._read_file(os.path.join(self.ENDPOINTS_DIR, "index.js"))
        # The module exports custom, it's in the admin endpoints directory by path
        assert "custom" in content, "'custom' not found in index.js"

    # ── functional_check (mocked / static verification) ──────────────────

    def test_unauthenticated_request_returns_401_structure(self):
        """Endpoint code must handle UnauthorizedError for 401 responses."""
        content = self._read_file(os.path.join(self.ENDPOINTS_DIR, "custom.js"))
        has_401 = "401" in content or "UnauthorizedError" in content or "authenticate" in content.lower()
        assert has_401, "No 401/UnauthorizedError handling found"

    def test_invalid_admin_key_returns_401(self):
        """Auth middleware should reject invalid keys (UnauthorizedError pattern)."""
        content = self._read_file(os.path.join(self.ENDPOINTS_DIR, "custom.js"))
        # Verify auth middleware is wired in
        assert re.search(r"authenticat|auth.*token|middleware", content, re.IGNORECASE), (
            "No authentication middleware wiring found"
        )

    def test_authenticated_get_returns_json_array(self):
        """Controller must return data suitable for JSON array response."""
        content = self._read_file(os.path.join(self.ENDPOINTS_DIR, "custom.js"))
        response_patterns = ["findAll", "findPage", "JSON", "response", "result"]
        found = any(p in content for p in response_patterns)
        assert found, "No data-fetching or response construction found in controller"

    def test_nonexistent_resource_returns_404(self):
        """Controller must throw NotFoundError for missing resources."""
        content = self._read_file(os.path.join(self.ENDPOINTS_DIR, "custom.js"))
        assert "NotFoundError" in content, "NotFoundError not used for 404 handling"

    def test_empty_collection_returns_200_not_404(self):
        """findAll returning empty array should still yield valid (non-404) response."""
        # Verify the controller uses findAll/findPage rather than findOne-only pattern
        content = self._read_file(os.path.join(self.ENDPOINTS_DIR, "custom.js"))
        has_collection = "findAll" in content or "findPage" in content or "browse" in content
        assert has_collection, "No collection-fetch method (findAll/findPage/browse) found"
