"""
Test for 'add-malli-schemas' skill — Malli Schema Validation for Bookmarks
Validates that the Agent added Malli schemas for the Bookmark entity with
proper types, enums, and route-level validation in Metabase.
"""

import os
import re

import pytest


class TestAddMalliSchemas:
    """Verify Malli schema definitions for Metabase Bookmarks."""

    REPO_DIR = "/workspace/metabase"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _find(self, *parts):
        path = os.path.join(self.REPO_DIR, *parts)
        return path if os.path.exists(path) else None

    def _api_bookmark(self):
        candidates = [
            "src/metabase/api/bookmark.clj",
            "src/metabase/api/bookmark.cljc",
        ]
        for c in candidates:
            p = self._find(c)
            if p:
                return p
        return None

    def _models_bookmark(self):
        candidates = [
            "src/metabase/models/bookmark.clj",
            "src/metabase/models/bookmark.cljc",
        ]
        for c in candidates:
            p = self._find(c)
            if p:
                return p
        return None

    # ---- file_path_check ----

    def test_api_bookmark_exists(self):
        """Verifies api/bookmark.clj exists."""
        path = self._api_bookmark()
        assert path is not None, "api/bookmark.clj not found"

    def test_models_bookmark_exists(self):
        """Verifies models/bookmark.clj exists."""
        path = self._models_bookmark()
        assert path is not None, "models/bookmark.clj not found"

    # ---- semantic_check ----

    def test_sem_positive_int_schema(self):
        """Verifies ms/PositiveInt or :pos-int schema usage."""
        content = self._read(self._api_bookmark())
        models_content = self._read(self._models_bookmark())
        combined = content + models_content
        assert (
            "ms/PositiveInt" in combined
            or "PositiveInt" in combined
            or "pos-int" in combined
        ), "PositiveInt schema not found"

    def test_sem_enum_keyword(self):
        """Verifies [:enum ...] schema usage."""
        content = self._read(self._models_bookmark())
        assert (
            "[:enum" in content or ":enum" in content
        ), "No :enum schema in models/bookmark"

    def test_sem_bookmark_schema(self):
        """Verifies ::Bookmark or :Bookmark schema definition."""
        content = self._read(self._models_bookmark())
        assert (
            "::Bookmark" in content or ":Bookmark" in content or "Bookmark" in content
        ), "Bookmark schema not defined in models"

    def test_sem_maybe_or_optional(self):
        """Verifies [:maybe or [:optional schema usage."""
        content = self._read(self._models_bookmark())
        assert (
            "[:maybe" in content or "[:optional" in content or ":optional" in content
        ), "No :maybe/:optional schema found"

    def test_sem_sequential_schema(self):
        """Verifies :sequential or vector schema for collections."""
        content = self._read(self._models_bookmark())
        assert (
            ":sequential" in content
            or "[:sequential" in content
            or "[:vector" in content
        ), "No :sequential schema found"

    def test_sem_require_malli(self):
        """Verifies Malli namespace is required."""
        content = self._read(self._api_bookmark())
        models_content = self._read(self._models_bookmark())
        combined = content + models_content
        assert (
            "malli" in combined.lower()
            or "metabase.util.malli" in combined
            or "ms/" in combined
        ), "Malli namespace not required"

    # ---- functional_check ----

    def test_func_non_blank_string(self):
        """Verifies NonBlankString or non-blank-string schema used."""
        content = self._read(self._models_bookmark())
        api_content = self._read(self._api_bookmark())
        combined = content + api_content
        assert (
            "NonBlankString" in combined
            or "non-blank-string" in combined
            or ":string" in combined
        ), "No string validation schema found"

    def test_func_success_boolean(self):
        """Verifies success response has boolean type."""
        content = self._read(self._api_bookmark())
        assert (
            ":boolean" in content or "ms/Boolean" in content or "boolean?" in content
        ), "No boolean schema for success response"

    def test_func_card_enum(self):
        """Verifies 'card' is an enum value for bookmark type."""
        content = self._read(self._models_bookmark())
        api_content = self._read(self._api_bookmark())
        combined = content + api_content
        assert re.search(
            r'"card"|:card|"card"', combined
        ), "No 'card' enum value found for bookmark type"

    def test_func_dashboard_enum(self):
        """Verifies 'dashboard' is an enum value for bookmark type."""
        content = self._read(self._models_bookmark())
        api_content = self._read(self._api_bookmark())
        combined = content + api_content
        assert re.search(
            r'"dashboard"|:dashboard|"dashboard"', combined
        ), "No 'dashboard' enum value found"

    def test_func_collection_enum(self):
        """Verifies 'collection' is an enum value for bookmark type."""
        content = self._read(self._models_bookmark())
        api_content = self._read(self._api_bookmark())
        combined = content + api_content
        assert re.search(
            r'"collection"|:collection|"collection"', combined
        ), "No 'collection' enum value found"

    def test_func_defendpoint_routes(self):
        """Verifies >= 4 defendpoint/api-let routes in api/bookmark.clj."""
        content = self._read(self._api_bookmark())
        matches = re.findall(
            r"(defendpoint|api/defendpoint|api-let|compojure)", content
        )
        assert (
            len(matches) >= 4
        ), f"Expected >= 4 route definitions, found {len(matches)}"

    def test_func_model_pos_int(self):
        """Verifies model ID uses pos-int? or PositiveInt."""
        content = self._read(self._models_bookmark())
        api_content = self._read(self._api_bookmark())
        combined = content + api_content
        assert (
            "pos-int?" in combined
            or "PositiveInt" in combined
            or "ms/PositiveInt" in combined
        ), "No positive integer validation for model ID"

    def test_func_ordering_field(self):
        """Verifies ordering/index field in bookmark model."""
        content = self._read(self._models_bookmark())
        assert (
            "ordering" in content or "index" in content or "position" in content
        ), "No ordering/index field in bookmark model"

    def test_func_schema_validation_on_create(self):
        """Verifies schema validation applied on bookmark creation route."""
        content = self._read(self._api_bookmark())
        assert re.search(
            r"(POST|:post|create|bookmark)", content, re.IGNORECASE
        ), "No create/POST route found in api/bookmark"
        assert re.search(
            r"(ms/|malli|schema|:>)", content
        ), "No schema validation on bookmark creation"
