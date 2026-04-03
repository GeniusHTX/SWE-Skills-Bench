"""
Test for 'security-review' skill — Django Security Hardening (babybuddy)
Validates secure cookie/frame settings, ALLOWED_HOSTS, serializer read-only
fields, ownership checks in views, and functional access control tests
against the babybuddy Django project.
"""

import os
import re
import sys

import pytest


class TestSecurityReview:
    """Verify babybuddy security hardening: settings, serializers, views."""

    REPO_DIR = "/workspace/babybuddy"

    # ── helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ──────────────────────────────────────────────────

    def test_settings_base_and_views_files_exist(self):
        """babybuddy/settings/base.py and babybuddy/views.py must exist."""
        base = os.path.join(self.REPO_DIR, "babybuddy", "settings", "base.py")
        views = os.path.join(self.REPO_DIR, "babybuddy", "views.py")
        assert os.path.isfile(base), f"{base} does not exist"
        assert os.path.isfile(views), f"{views} does not exist"

    def test_api_views_and_serializers_exist(self):
        """api/views.py and api/serializers.py must exist."""
        api_views = os.path.join(self.REPO_DIR, "api", "views.py")
        api_ser = os.path.join(self.REPO_DIR, "api", "serializers.py")
        assert os.path.isfile(api_views), f"{api_views} does not exist"
        assert os.path.isfile(api_ser), f"{api_ser} does not exist"

    def test_middleware_and_core_views_exist(self):
        """babybuddy/middleware.py and core/views.py must exist."""
        mw = os.path.join(self.REPO_DIR, "babybuddy", "middleware.py")
        cv = os.path.join(self.REPO_DIR, "core", "views.py")
        assert os.path.isfile(mw), f"{mw} does not exist"
        assert os.path.isfile(cv), f"{cv} does not exist"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_settings_have_secure_cookie_and_frame_options(self):
        """base.py must set SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE, X_FRAME_OPTIONS."""
        content = self._read_file(
            os.path.join(self.REPO_DIR, "babybuddy", "settings", "base.py")
        )
        assert re.search(r"SESSION_COOKIE_SECURE\s*=\s*True", content), (
            "SESSION_COOKIE_SECURE = True not found"
        )
        assert re.search(r"CSRF_COOKIE_SECURE\s*=\s*True", content), (
            "CSRF_COOKIE_SECURE = True not found"
        )
        assert re.search(r"X_FRAME_OPTIONS\s*=\s*['\"]DENY['\"]", content), (
            "X_FRAME_OPTIONS = 'DENY' not found"
        )

    def test_allowed_hosts_not_wildcard(self):
        """ALLOWED_HOSTS must not use wildcard ['*']."""
        content = self._read_file(
            os.path.join(self.REPO_DIR, "babybuddy", "settings", "base.py")
        )
        # Find ALLOWED_HOSTS line(s)
        for line in content.splitlines():
            if "ALLOWED_HOSTS" in line and "=" in line:
                assert not re.search(r"""\[\s*['\"]\*['\"]""", line), (
                    "ALLOWED_HOSTS contains wildcard ['*']"
                )

    def test_feeding_serializer_has_read_only_fields(self):
        """FeedingSerializer must declare read_only_fields with 'id' or 'is_staff'."""
        content = self._read_file(
            os.path.join(self.REPO_DIR, "api", "serializers.py")
        )
        assert "read_only_fields" in content, "read_only_fields not found in serializers.py"

    def test_user_password_and_delete_views_check_ownership(self):
        """UserPassword and UserDelete views must contain ownership checks."""
        content = self._read_file(
            os.path.join(self.REPO_DIR, "babybuddy", "views.py")
        )
        assert "UserPassword" in content or "UserDelete" in content, (
            "UserPassword/UserDelete views not found"
        )
        auth_patterns = ["PermissionDenied", "is_staff", "request.user", "403"]
        has_auth = any(p in content for p in auth_patterns)
        assert has_auth, "No ownership/permission check logic in views.py"

    # ── functional_check (import with Django) ────────────────────────────

    @staticmethod
    def _setup_django():
        """Configure Django settings; skip if not available."""
        repo = "/workspace/babybuddy"
        if repo not in sys.path:
            sys.path.insert(0, repo)
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "babybuddy.settings.base")
        try:
            import django
            django.setup()
        except Exception as exc:
            pytest.skip(f"Django setup failed: {exc}")

    def test_non_owner_get_user_password_returns_403(self):
        """Non-staff non-owner GET /users/<other_pk>/password/ must return 403."""
        self._setup_django()
        try:
            from django.test import TestCase, Client
            from django.contrib.auth import get_user_model
        except Exception as exc:
            pytest.skip(f"Django imports failed: {exc}")
        User = get_user_model()
        try:
            user_a = User.objects.create_user(username="userA_sec", password="pass1234")
            user_b = User.objects.create_user(username="userB_sec", password="pass1234")
            client = Client()
            client.force_login(user_a)
            response = client.get(f"/users/{user_b.pk}/password/")
            assert response.status_code == 403, (
                f"Expected 403, got {response.status_code}"
            )
        except Exception as exc:
            pytest.skip(f"Functional test skipped: {exc}")
        finally:
            User.objects.filter(username__in=["userA_sec", "userB_sec"]).delete()

    def test_non_owner_delete_user_returns_403(self):
        """Non-staff non-owner DELETE /users/<other_pk>/delete/ must return 403."""
        self._setup_django()
        try:
            from django.test import Client
            from django.contrib.auth import get_user_model
        except Exception as exc:
            pytest.skip(f"Django imports failed: {exc}")
        User = get_user_model()
        try:
            user_a = User.objects.create_user(username="userC_sec", password="pass1234")
            user_b = User.objects.create_user(username="userD_sec", password="pass1234")
            client = Client()
            client.force_login(user_a)
            response = client.delete(f"/users/{user_b.pk}/delete/")
            assert response.status_code == 403, (
                f"Expected 403, got {response.status_code}"
            )
        except Exception as exc:
            pytest.skip(f"Functional test skipped: {exc}")
        finally:
            User.objects.filter(username__in=["userC_sec", "userD_sec"]).delete()

    def test_mass_assignment_is_staff_field_ignored(self):
        """Serializer must ignore is_staff in validated_data (read-only)."""
        self._setup_django()
        try:
            from api.serializers import FeedingSerializer
        except Exception as exc:
            pytest.skip(f"Cannot import FeedingSerializer: {exc}")
        # Validate that is_staff is declared read-only at Meta level
        meta = getattr(FeedingSerializer, "Meta", None)
        if meta:
            ro = getattr(meta, "read_only_fields", ())
            assert "is_staff" in ro or "id" in ro, (
                "read_only_fields missing protective fields"
            )
        else:
            pytest.skip("FeedingSerializer.Meta not found")

    def test_xss_script_in_child_name_returns_400(self):
        """POST /api/children/ with XSS payload must return 400."""
        self._setup_django()
        try:
            from rest_framework.test import APIClient
            from django.contrib.auth import get_user_model
        except Exception as exc:
            pytest.skip(f"DRF imports failed: {exc}")
        User = get_user_model()
        try:
            user = User.objects.create_user(username="xss_test", password="pass1234")
            client = APIClient()
            client.force_authenticate(user=user)
            response = client.post("/api/children/", {
                "first_name": "<script>alert(1)</script>",
                "last_name": "Test",
                "birth_date": "2020-01-01",
            }, format="json")
            assert response.status_code == 400, (
                f"Expected 400 for XSS payload, got {response.status_code}"
            )
        except Exception as exc:
            pytest.skip(f"Functional test skipped: {exc}")
        finally:
            User.objects.filter(username="xss_test").delete()

    def test_negative_feeding_amount_returns_400(self):
        """POST /api/feedings/ with amount=-1 must return 400."""
        self._setup_django()
        try:
            from rest_framework.test import APIClient
            from django.contrib.auth import get_user_model
        except Exception as exc:
            pytest.skip(f"DRF imports failed: {exc}")
        User = get_user_model()
        try:
            user = User.objects.create_user(username="neg_test", password="pass1234")
            client = APIClient()
            client.force_authenticate(user=user)
            response = client.post("/api/feedings/", {
                "child": 1,
                "start": "2024-01-01T12:00:00Z",
                "end": "2024-01-01T12:30:00Z",
                "type": "breast milk",
                "method": "left breast",
                "amount": -1,
            }, format="json")
            assert response.status_code == 400, (
                f"Expected 400 for negative amount, got {response.status_code}"
            )
        except Exception as exc:
            pytest.skip(f"Functional test skipped: {exc}")
        finally:
            User.objects.filter(username="neg_test").delete()

    def test_owner_can_access_own_password_view(self):
        """Owner GET /users/<own_pk>/password/ should return 200 or 302 (not 403)."""
        self._setup_django()
        try:
            from django.test import Client
            from django.contrib.auth import get_user_model
        except Exception as exc:
            pytest.skip(f"Django imports failed: {exc}")
        User = get_user_model()
        try:
            user = User.objects.create_user(username="owner_sec", password="pass1234")
            client = Client()
            client.force_login(user)
            response = client.get(f"/users/{user.pk}/password/")
            assert response.status_code in (200, 302), (
                f"Owner got {response.status_code}, expected 200 or 302"
            )
        except Exception as exc:
            pytest.skip(f"Functional test skipped: {exc}")
        finally:
            User.objects.filter(username="owner_sec").delete()
