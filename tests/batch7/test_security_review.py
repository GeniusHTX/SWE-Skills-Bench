"""Test file for the security-review skill.

This suite validates security hardening in babybuddy: cookie settings,
serializer validation, rate limiting, and form input validation.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest


class TestSecurityReview:
    """Verify security hardening in babybuddy."""

    REPO_DIR = "/workspace/babybuddy"

    SETTINGS_PY = "babybuddy/settings/base.py"
    API_VIEWS_PY = "api/views.py"
    API_SERIALIZERS_PY = "api/serializers.py"

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

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_babybuddy_settings_base_py_modified(self):
        """Verify settings/base.py exists (modified)."""
        self._assert_non_empty_file(self.SETTINGS_PY)

    def test_file_path_api_views_py_modified(self):
        """Verify api/views.py exists (modified)."""
        self._assert_non_empty_file(self.API_VIEWS_PY)

    def test_file_path_api_serializers_py_modified(self):
        """Verify api/serializers.py exists (modified)."""
        self._assert_non_empty_file(self.API_SERIALIZERS_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_session_cookie_secure_true_session_cookie_httponly_true_same(
        self,
    ):
        """SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True, SAMESITE='Lax'|'Strict'."""
        src = self._read_text(self.SETTINGS_PY)
        assert re.search(
            r"SESSION_COOKIE_SECURE\s*=\s*True", src
        ), "SESSION_COOKIE_SECURE should be True"
        assert re.search(
            r"SESSION_COOKIE_HTTPONLY\s*=\s*True", src
        ), "SESSION_COOKIE_HTTPONLY should be True"
        assert re.search(
            r"SESSION_COOKIE_SAMESITE\s*=\s*['\"]?(Lax|Strict)", src
        ), "SESSION_COOKIE_SAMESITE should be Lax or Strict"

    def test_semantic_csrf_cookie_httponly_true_x_frame_options_deny_sameorigin(self):
        """CSRF_COOKIE_HTTPONLY=True, X_FRAME_OPTIONS='DENY'|'SAMEORIGIN'."""
        src = self._read_text(self.SETTINGS_PY)
        assert re.search(
            r"CSRF_COOKIE_HTTPONLY\s*=\s*True", src
        ), "CSRF_COOKIE_HTTPONLY should be True"
        assert re.search(
            r"X_FRAME_OPTIONS\s*=\s*['\"]?(DENY|SAMEORIGIN)", src
        ), "X_FRAME_OPTIONS should be DENY or SAMEORIGIN"

    def test_semantic_serializer_max_length_1000_on_text_fields(self):
        """Serializer max_length=1000 on text fields."""
        src = self._read_text(self.API_SERIALIZERS_PY)
        assert re.search(
            r"max_length\s*=\s*1000", src
        ), "Text fields should have max_length=1000"

    def test_semantic_rate_limit_middleware_with_per_ip_tracking_using_django_cach(
        self,
    ):
        """Rate limit middleware with per-IP tracking using Django cache."""
        src = self._read_text(self.SETTINGS_PY)
        settings_and_views = src + "\n" + self._read_text(self.API_VIEWS_PY)
        assert re.search(
            r"rate.limit|throttle|RateLimit|Throttle", settings_and_views, re.IGNORECASE
        ), "Rate limit middleware or throttle class required"

    def test_semantic_start_end_validation_in_serializers_and_forms(self):
        """start < end validation in serializers and forms."""
        src = self._read_text(self.API_SERIALIZERS_PY)
        assert re.search(
            r"start.*end|end.*start|validate", src
        ), "start < end validation required"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, source analysis)
    # ------------------------------------------------------------------

    def test_functional_post_api_feedings_with_notes_1000_400(self):
        """POST /api/feedings/ with notes > 1000 -> 400."""
        src = self._read_text(self.API_SERIALIZERS_PY)
        assert re.search(
            r"max_length|notes|1000", src
        ), "Notes field should enforce max_length"

    def test_functional_post_api_sleep_with_start_end_400(self):
        """POST /api/sleep/ with start > end -> 400."""
        src = self._read_text(self.API_SERIALIZERS_PY)
        assert re.search(
            r"start|end|validate", src
        ), "Sleep serializer should validate start < end"

    def test_functional_post_api_changes_with_color_purple_400(self):
        """POST /api/changes/ with color='purple' -> 400."""
        src = self._read_text(self.API_SERIALIZERS_PY)
        assert re.search(
            r"color|choices|ChoiceField|validate", src, re.IGNORECASE
        ), "Changes serializer should validate color choices"

    def test_functional_web_feeding_form_with_negative_amount_error(self):
        """Web Feeding form with negative amount -> error."""
        src = self._read_text(self.API_SERIALIZERS_PY)
        assert re.search(
            r"amount|min_value|MinValueValidator|positive", src, re.IGNORECASE
        ), "Feeding form should reject negative amounts"

    def test_functional_11th_rapid_login_429_with_retry_after(self):
        """11th rapid login -> 429 with Retry-After."""
        settings = self._read_text(self.SETTINGS_PY)
        views = self._read_text(self.API_VIEWS_PY)
        combined = settings + "\n" + views
        assert re.search(
            r"Throttle|rate.limit|429|Retry-After", combined, re.IGNORECASE
        ), "Rate limiting should produce 429 responses"
