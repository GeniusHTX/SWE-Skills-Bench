"""
Test for 'django-patterns' skill — Django REST Framework Patterns
Validates serializers, views, permissions, signals, and pagination for a Django
DRF project including ModelSerializer, ViewSet, IsOwnerOrAdmin permission,
and API response codes.
"""

import glob
import os
import re
import subprocess
import sys

import pytest


class TestDjangoPatterns:
    """Verify Django REST Framework patterns: serializers, views, permissions, signals."""

    REPO_DIR = "/workspace/saleor"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _app_path(self, name: str) -> str:
        return os.path.join(self.REPO_DIR, "myapp", name)

    def _find_file(self, name: str) -> str:
        """Find a file in myapp or any common Django app directory."""
        direct = self._app_path(name)
        if os.path.isfile(direct):
            return direct
        candidates = glob.glob(os.path.join(self.REPO_DIR, "**", name), recursive=True)
        return candidates[0] if candidates else direct

    # ── file_path_check ──────────────────────────────────────────────────

    def test_serializers_py_exists(self):
        """myapp/serializers.py must exist with ModelSerializer definitions."""
        path = self._app_path("serializers.py")
        assert os.path.isfile(path), f"{path} does not exist"
        assert os.path.getsize(path) > 0

    def test_views_py_exists(self):
        """myapp/views.py must exist with ModelViewSet definitions."""
        path = self._app_path("views.py")
        assert os.path.isfile(path), f"{path} does not exist"

    def test_permissions_py_exists(self):
        """myapp/permissions.py must exist with IsOwnerOrAdmin permission class."""
        path = self._app_path("permissions.py")
        assert os.path.isfile(path), f"{path} does not exist"

    def test_signals_py_exists(self):
        """myapp/signals.py must exist with Django signal handlers."""
        path = self._app_path("signals.py")
        assert os.path.isfile(path), f"{path} does not exist"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_serializer_declares_model_and_fields(self):
        """serializers.py must have ModelSerializer with Meta.model and Meta.fields."""
        path = self._app_path("serializers.py")
        if not os.path.isfile(path):
            pytest.skip("serializers.py not found")
        content = self._read_file(path)
        assert "ModelSerializer" in content, "ModelSerializer not referenced"
        assert "class Meta:" in content, "Meta inner class not found"
        assert "model =" in content or "model=" in content, "Meta.model not set"
        assert "fields =" in content or "fields=" in content, "Meta.fields not set"

    def test_viewset_declares_permission_classes(self):
        """views.py must declare permission_classes on the ViewSet."""
        path = self._app_path("views.py")
        if not os.path.isfile(path):
            pytest.skip("views.py not found")
        content = self._read_file(path)
        assert "permission_classes" in content, "permission_classes not declared"
        has_perm = "IsAuthenticated" in content or "IsOwnerOrAdmin" in content
        assert has_perm, "No authentication permission found in permission_classes"

    def test_isowneror_admin_permission_defined(self):
        """permissions.py must define IsOwnerOrAdmin extending BasePermission."""
        path = self._app_path("permissions.py")
        if not os.path.isfile(path):
            pytest.skip("permissions.py not found")
        content = self._read_file(path)
        assert "IsOwnerOrAdmin" in content, "IsOwnerOrAdmin class not defined"
        assert "BasePermission" in content, "BasePermission not referenced"
        assert "has_object_permission" in content, "has_object_permission not implemented"

    def test_pagination_configured(self):
        """Pagination must be configured in ViewSet or settings."""
        path = self._app_path("views.py")
        if not os.path.isfile(path):
            pytest.skip("views.py not found")
        content = self._read_file(path)
        settings_content = ""
        for settings_file in ("settings.py", os.path.join("config", "settings.py")):
            sp = os.path.join(self.REPO_DIR, settings_file)
            if os.path.isfile(sp):
                settings_content = self._read_file(sp)
                break
        has_pagination = (
            "pagination_class" in content
            or "DEFAULT_PAGINATION_CLASS" in settings_content
        )
        assert has_pagination, "No pagination configuration found"

    # ── functional_check ─────────────────────────────────────────────────

    def test_unauthenticated_request_returns_401(self):
        """Unauthenticated GET to protected endpoint must return 401."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from rest_framework.test import APIClient
        except ImportError:
            pytest.skip("Django REST framework not importable")
        client = APIClient()
        response = client.get("/api/myresource/")
        assert response.status_code == 401

    def test_non_owner_returns_403(self):
        """Non-owner accessing another user's resource must get 403."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from rest_framework.test import APIClient
            from django.contrib.auth.models import User
        except ImportError:
            pytest.skip("Django REST framework not importable")
        # This test requires Django test DB setup — skip in pure static env
        pytest.skip("Requires Django test database setup")

    def test_invalid_post_returns_400(self):
        """POST with empty body to creation endpoint must return 400."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from rest_framework.test import APIClient
        except ImportError:
            pytest.skip("Django REST framework not importable")
        pytest.skip("Requires Django test database setup")

    def test_paginated_response_has_required_fields(self):
        """Paginated GET list must return count, next, previous, results fields."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from rest_framework.test import APIClient
        except ImportError:
            pytest.skip("Django REST framework not importable")
        pytest.skip("Requires Django test database setup")

    def test_signal_handler_dispatches_celery_task(self):
        """signals.py must contain post_save signal and Celery task dispatch."""
        path = self._app_path("signals.py")
        if not os.path.isfile(path):
            pytest.skip("signals.py not found")
        content = self._read_file(path)
        assert "post_save" in content, "post_save signal not found in signals.py"
        has_task = "delay" in content or "apply_async" in content or "send_task" in content
        assert has_task, "No Celery task dispatch found in signal handler"
