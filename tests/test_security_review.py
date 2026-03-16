"""
Test for 'security-review' skill — Secure Export API for BabyBuddy
Validates that the Agent implemented authenticated, authorized export endpoints
with proper serializers, views, URLs, and security checks.
"""

import os
import ast
import subprocess
import pytest

from _dependency_utils import ensure_python_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_python_dependencies(TestSecurityReview.REPO_DIR)


class TestSecurityReview:
    """Verify secure data export endpoint implementation for BabyBuddy."""

    REPO_DIR = "/workspace/babybuddy"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_serializers_file_exists(self):
        """api/serializers.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "api", "serializers.py")
        assert os.path.isfile(fpath), "api/serializers.py not found"

    def test_views_file_exists(self):
        """api/views.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "api", "views.py")
        assert os.path.isfile(fpath), "api/views.py not found"

    def test_urls_file_exists(self):
        """api/urls.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "api", "urls.py")
        assert os.path.isfile(fpath), "api/urls.py not found"

    # ------------------------------------------------------------------
    # L2: functional verification
    # ------------------------------------------------------------------

    def test_feeding_export_serializer_defined(self):
        """FeedingExportSerializer must be defined in api/serializers.py."""
        fpath = os.path.join(self.REPO_DIR, "api", "serializers.py")
        with open(fpath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        class_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        assert (
            "FeedingExportSerializer" in class_names
        ), f"FeedingExportSerializer not found; classes: {class_names}"

    def test_sleep_export_serializer_defined(self):
        """SleepExportSerializer must be defined in api/serializers.py."""
        fpath = os.path.join(self.REPO_DIR, "api", "serializers.py")
        with open(fpath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        class_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        assert (
            "SleepExportSerializer" in class_names
        ), f"SleepExportSerializer not found; classes: {class_names}"

    def test_feeding_serializer_fields(self):
        """FeedingExportSerializer must include required fields."""
        fpath = os.path.join(self.REPO_DIR, "api", "serializers.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        required = ["id", "start", "end", "duration", "type", "method", "amount"]
        for field in required:
            assert field in content, f"Field '{field}' not found in serializers.py"

    def test_sleep_serializer_fields(self):
        """SleepExportSerializer must include required fields."""
        fpath = os.path.join(self.REPO_DIR, "api", "serializers.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        required = ["id", "start", "end", "duration"]
        for field in required:
            assert field in content, f"Field '{field}' not found in serializers.py"

    def test_export_viewset_defined(self):
        """ExportViewSet (or similar) must be defined in api/views.py."""
        fpath = os.path.join(self.REPO_DIR, "api", "views.py")
        with open(fpath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        class_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        export_views = [c for c in class_names if "export" in c.lower()]
        assert (
            len(export_views) >= 1
        ), f"No export-related ViewSet found; classes: {class_names}"

    def test_authentication_enforced(self):
        """Views must enforce authentication (IsAuthenticated or similar)."""
        fpath = os.path.join(self.REPO_DIR, "api", "views.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        auth_patterns = [
            "IsAuthenticated",
            "permission_classes",
            "authentication_classes",
        ]
        found = any(p in content for p in auth_patterns)
        assert found, "No authentication enforcement found in views.py"

    def test_export_route_registered(self):
        """Export route must be registered in api/urls.py."""
        fpath = os.path.join(self.REPO_DIR, "api", "urls.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert "export" in content.lower(), "No export route registered in urls.py"

    def test_django_system_check(self):
        """python manage.py check should pass without errors."""
        result = subprocess.run(
            ["python", "manage.py", "check"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"Django check failed:\n{result.stderr}"

    def test_child_ownership_validation(self):
        """Views must validate child ownership (403 for other user's child)."""
        fpath = os.path.join(self.REPO_DIR, "api", "views.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        ownership_patterns = [
            "child",
            "403",
            "Forbidden",
            "get_object_or_404",
            "request.user",
            "filter",
            "permission",
        ]
        found_count = sum(1 for p in ownership_patterns if p in content)
        assert found_count >= 3, (
            f"Insufficient ownership validation logic in views.py "
            f"(matched {found_count}/6 patterns)"
        )

    def test_api_tests_exist(self):
        """Test file for the export API must exist."""
        candidates = [
            os.path.join(self.REPO_DIR, "tests", "test_api.py"),
            os.path.join(self.REPO_DIR, "api", "tests.py"),
            os.path.join(self.REPO_DIR, "babybuddy", "tests", "test_api.py"),
        ]
        found = any(os.path.isfile(c) for c in candidates)
        assert found, f"No API test file found among {candidates}"
