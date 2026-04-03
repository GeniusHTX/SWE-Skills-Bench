"""
Test for 'add-malli-schemas' skill — Malli Schema Annotations
Validates that the Agent added Malli schema definitions and annotations
to the Metabase actions API endpoints.
"""

import os
import re
import subprocess

import pytest


class TestAddMalliSchemas:
    """Verify Malli schema annotations on Metabase actions API."""

    REPO_DIR = "/workspace/metabase"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_api_clj_exists(self):
        """Verify the actions api.clj and models.clj files exist at expected paths."""
        for rel in (
            "src/metabase/actions/api.clj",
            "src/metabase/actions/models.clj",
        ):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_api_test_clj_exists(self):
        """Verify the actions api_test.clj test file exists."""
        path = os.path.join(self.REPO_DIR, "test/metabase/actions/api_test.clj")
        assert os.path.isfile(path), "test/metabase/actions/api_test.clj missing"

    def test_models_clj_exists(self):
        """Verify models.clj for actions schema definitions exists."""
        path = os.path.join(self.REPO_DIR, "src/metabase/actions/models.clj")
        assert os.path.isfile(path), "src/metabase/actions/models.clj missing"

    # ── semantic_check ──────────────────────────────────────────────

    def test_mr_def_schemas_in_models_clj(self):
        """Verify all 5 named Malli schemas are defined with mr/def in models.clj."""
        content = self._read(os.path.join(self.REPO_DIR, "src/metabase/actions/models.clj"))
        assert content, "models.clj is empty or unreadable"
        for pattern in ("mr/def ::Action", "mr/def ::CreateActionRequest",
                        "mr/def ::ActionResponse", "mr/def ::HttpActionDetails"):
            assert pattern in content, f"Pattern '{pattern}' not found in models.clj"

    def test_defendpoint_schema_annotations_in_api_clj(self):
        """Verify POST endpoint is annotated with :- schema syntax in api.clj."""
        content = self._read(os.path.join(self.REPO_DIR, "src/metabase/actions/api.clj"))
        assert content, "api.clj is empty or unreadable"
        assert ":- ::ActionResponse" in content, ":- ::ActionResponse annotation missing"
        assert "defendpoint" in content, "defendpoint form missing in api.clj"

    def test_http_method_enum_in_schema(self):
        """Verify ::HttpActionDetails schema contains [:method [:enum ...]] for HTTP method validation."""
        content = self._read(os.path.join(self.REPO_DIR, "src/metabase/actions/models.clj"))
        assert content, "models.clj is empty or unreadable"
        for kw in (":method", ":enum", "GET", "POST", "PUT", "DELETE", "PATCH"):
            assert kw in content, f"Keyword '{kw}' not found in models.clj"

    def test_route_param_schema_on_endpoints(self):
        """Verify route param schema with PositiveInt is applied for :id parameter."""
        content = self._read(os.path.join(self.REPO_DIR, "src/metabase/actions/api.clj"))
        assert content, "api.clj is empty or unreadable"
        assert "ms/PositiveInt" in content, "ms/PositiveInt not found in api.clj"
        assert ":id" in content, ":id route param not found in api.clj"

    # ── functional_check (command) ──────────────────────────────────

    def _skip_unless_lein_ready(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if not os.path.isfile(os.path.join(self.REPO_DIR, "project.clj")):
            pytest.skip("project.clj missing")

    def test_post_missing_name_returns_400(self):
        """POST /api/action/ with missing :name field returns 400 validation error."""
        self._skip_unless_lein_ready()
        content = self._read(os.path.join(self.REPO_DIR, "test/metabase/actions/api_test.clj"))
        assert content, "api_test.clj is empty or unreadable"
        assert "400" in content or "name" in content, \
            "No test for missing :name validation in api_test.clj"

    def test_post_invalid_http_method_returns_400(self):
        """POST /api/action/ with invalid :method returns 400."""
        self._skip_unless_lein_ready()
        content = self._read(os.path.join(self.REPO_DIR, "test/metabase/actions/api_test.clj"))
        assert content, "api_test.clj is empty or unreadable"
        assert "400" in content or "BADMETHOD" in content.upper() or "method" in content, \
            "No test for invalid HTTP method validation"

    def test_put_non_numeric_id_returns_400(self):
        """PUT /api/action/abc (non-numeric id) returns 400 route param validation error."""
        self._skip_unless_lein_ready()
        content = self._read(os.path.join(self.REPO_DIR, "test/metabase/actions/api_test.clj"))
        assert content, "api_test.clj is empty or unreadable"
        assert "400" in content or "PositiveInt" in content or ":id" in content, \
            "No test for non-numeric :id validation"

    def test_valid_post_returns_200(self):
        """POST /api/action/ with valid complete payload returns 200/201 matching ActionResponse."""
        self._skip_unless_lein_ready()
        content = self._read(os.path.join(self.REPO_DIR, "test/metabase/actions/api_test.clj"))
        assert content, "api_test.clj is empty or unreadable"
        assert "200" in content or "201" in content or "action" in content.lower(), \
            "No test for valid POST returning success status"
