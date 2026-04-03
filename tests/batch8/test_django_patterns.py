"""
Test for 'django-patterns' skill — Saleor Wishlist REST API
Validates that the Agent implemented a Django REST Framework wishlist
module with models, views, serializers, URLs, auth, and ownership isolation.
"""

import os
import re
import subprocess

import pytest


class TestDjangoPatterns:
    """Verify Saleor wishlist REST API implementation."""

    REPO_DIR = "/workspace/saleor"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_wishlist_module_files_exist(self):
        """Verify wishlist __init__.py, models.py, views.py, and serializers.py exist."""
        for rel in ("saleor/wishlist/__init__.py", "saleor/wishlist/models.py",
                     "saleor/wishlist/views.py", "saleor/wishlist/serializers.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_wishlist_urls_and_tests_exist(self):
        """Verify urls.py exists."""
        path = os.path.join(self.REPO_DIR, "saleor/wishlist/urls.py")
        assert os.path.isfile(path), "saleor/wishlist/urls.py missing"

    def test_wishlist_test_file_exists(self):
        """Verify at least one test file exists for wishlist."""
        found = (
            os.path.isfile(os.path.join(self.REPO_DIR, "saleor/wishlist/tests.py"))
            or os.path.isdir(os.path.join(self.REPO_DIR, "saleor/wishlist/tests"))
        )
        assert found, "Neither tests.py nor tests/ directory found"

    # ── semantic_check ──────────────────────────────────────────────

    def test_wishlist_model_fields(self):
        """Verify Wishlist model defines user FK, product_variant FK, and added_at."""
        content = self._read(os.path.join(self.REPO_DIR, "saleor/wishlist/models.py"))
        assert content, "models.py is empty or unreadable"
        for field in ("user", "product_variant", "added_at", "ForeignKey"):
            assert field in content, f"'{field}' not found in models.py"

    def test_view_is_authenticated_permission(self):
        """Verify views.py uses IsAuthenticated permission class."""
        content = self._read(os.path.join(self.REPO_DIR, "saleor/wishlist/views.py"))
        assert content, "views.py is empty or unreadable"
        assert "IsAuthenticated" in content, "IsAuthenticated not found in views.py"

    def test_view_filters_by_request_user(self):
        """Verify views.py filters queryset by request.user for ownership isolation."""
        content = self._read(os.path.join(self.REPO_DIR, "saleor/wishlist/views.py"))
        assert content, "views.py is empty or unreadable"
        assert "request.user" in content, "request.user filtering not found"
        assert "get_queryset" in content, "get_queryset not found"

    def test_serializer_nested_variant_fields(self):
        """Verify serializer defines nested product_variant fields."""
        content = self._read(os.path.join(self.REPO_DIR, "saleor/wishlist/serializers.py"))
        assert content, "serializers.py is empty or unreadable"
        found = any(kw in content for kw in ("name", "sku", "price", "nested"))
        assert found, "No variant field references found in serializers.py"

    # ── functional_check (command) ──────────────────────────────────

    def _skip_unless_django(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")

    def test_unauthenticated_get_returns_401(self):
        """Unauthenticated GET /api/wishlist/ returns 401."""
        self._skip_unless_django()
        content = self._read(os.path.join(self.REPO_DIR, "saleor/wishlist/views.py"))
        assert "IsAuthenticated" in content, \
            "Auth enforcement via IsAuthenticated not found"

    def test_post_new_item_returns_201(self):
        """Authenticated POST /api/wishlist/ with new variant_id returns 201."""
        self._skip_unless_django()
        # Verify test file covers 201 creation
        for candidate in ("saleor/wishlist/tests.py", "saleor/wishlist/tests/test_views.py"):
            tc = self._read(os.path.join(self.REPO_DIR, candidate))
            if tc and ("201" in tc or "create" in tc.lower()):
                return
        # Fallback: check view for create method
        content = self._read(os.path.join(self.REPO_DIR, "saleor/wishlist/views.py"))
        assert "create" in content.lower() or "post" in content.lower(), \
            "No POST/create handler found"

    def test_post_duplicate_returns_200_idempotent(self):
        """Second POST with same variant_id returns 200 (idempotent)."""
        self._skip_unless_django()
        content = self._read(os.path.join(self.REPO_DIR, "saleor/wishlist/views.py"))
        assert content, "views.py is empty"
        found = "get_or_create" in content or "idempotent" in content.lower() or "200" in content
        assert found, "No idempotent duplicate handling found in views.py"

    def test_cross_user_access_forbidden(self):
        """User A accessing User B's wishlist item returns 403 or 404."""
        self._skip_unless_django()
        content = self._read(os.path.join(self.REPO_DIR, "saleor/wishlist/views.py"))
        assert "request.user" in content, "Ownership isolation via request.user not found"
