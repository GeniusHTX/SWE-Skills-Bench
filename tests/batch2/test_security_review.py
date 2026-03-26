"""
Test for 'security-review' skill — Security Review
Validates that the Agent added secure data export endpoints to the BabyBuddy
Django application with proper authentication, authorization, input validation,
and serializer-controlled field exposure.
"""

import os
import re
import subprocess

import pytest

from _dependency_utils import ensure_python_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_python_dependencies(TestSecurityReview.REPO_DIR)


class TestSecurityReview:
    """Verify secure data export endpoints in BabyBuddy."""

    REPO_DIR = "/workspace/babybuddy"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    def _find_file(self, *candidates):
        """Return contents of the first candidate that exists."""
        for parts in candidates:
            fpath = os.path.join(self.REPO_DIR, *parts)
            if os.path.isfile(fpath):
                with open(fpath, "r", errors="ignore") as fh:
                    return fh.read()
        paths = [os.path.join(*c) for c in candidates]
        pytest.fail(f"None of the expected files exist: {paths}")

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_views_file_exists(self):
        """api/views.py must exist (modified to add export views)."""
        fpath = os.path.join(self.REPO_DIR, "api", "views.py")
        assert os.path.isfile(fpath), "api/views.py not found"

    def test_serializers_file_exists(self):
        """api/serializers.py must exist (modified to add export serializers)."""
        fpath = os.path.join(self.REPO_DIR, "api", "serializers.py")
        assert os.path.isfile(fpath), "api/serializers.py not found"

    def test_urls_file_exists(self):
        """api/urls.py must exist (modified to register export URL patterns)."""
        fpath = os.path.join(self.REPO_DIR, "api", "urls.py")
        assert os.path.isfile(fpath), "api/urls.py not found"

    # ------------------------------------------------------------------
    # L1: Views contain export-related code
    # ------------------------------------------------------------------

    def test_views_contain_export_view(self):
        """api/views.py must define an export-related view class or function."""
        content = self._read("api", "views.py")
        patterns = [
            r"[Ee]xport",
            r"[Dd]ata[Ee]xport",
            r"export_",
            r"ExportView",
            r"ExportAPIView",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "api/views.py does not contain any export-related view definition"

    def test_views_use_authentication(self):
        """Export views must enforce authentication via DRF decorators or permission classes."""
        content = self._read("api", "views.py")
        auth_patterns = [
            r"IsAuthenticated",
            r"authentication_classes",
            r"permission_classes",
            r"@login_required",
            r"@api_view.*permission",
            r"LoginRequired",
            r"TokenAuthentication",
            r"SessionAuthentication",
        ]
        assert any(
            re.search(p, content) for p in auth_patterns
        ), "Export views do not appear to enforce authentication"

    def test_views_enforce_object_level_permissions(self):
        """Export views must enforce object-level authorization (user can only access their children)."""
        content = self._read("api", "views.py")
        authz_patterns = [
            r"get_queryset",
            r"request\.user",
            r"filter.*user",
            r"user.*filter",
            r"has_object_permission",
            r"check_object_permissions",
            r"ObjectPermission",
            r"PermissionDenied",
        ]
        assert any(
            re.search(p, content) for p in authz_patterns
        ), "Export views do not appear to enforce object-level permissions"

    # ------------------------------------------------------------------
    # L1: Serializer structure
    # ------------------------------------------------------------------

    def test_serializer_defines_export_fields(self):
        """api/serializers.py must define a serializer with explicit field list for exports."""
        content = self._read("api", "serializers.py")
        # Must have a fields attribute or Meta.fields
        has_export = bool(re.search(r"[Ee]xport", content))
        has_fields = bool(re.search(r"fields\s*=", content))
        assert has_export, "api/serializers.py does not contain export serializer"
        assert has_fields, "Export serializer does not declare explicit fields"

    def test_serializer_does_not_expose_all_fields(self):
        """Export serializer must not use fields = '__all__' — explicit field lists are required."""
        content = self._read("api", "serializers.py")
        # Search for field declarations near export-related code
        all_fields_pattern = re.findall(r"fields\s*=\s*['\"]__all__['\"]", content)
        # This is a heuristic — we flag it if __all__ is used anywhere in the file
        # since the task requires controlled field exposure
        if all_fields_pattern:
            # Check if it's specifically in an export serializer context
            export_section = re.search(
                r"class\s+\w*[Ee]xport\w*.*?(?=class\s|\Z)",
                content,
                re.DOTALL,
            )
            if export_section and "__all__" in export_section.group():
                pytest.fail(
                    "Export serializer uses fields='__all__' — "
                    "must explicitly list fields to prevent data leakage"
                )

    # ------------------------------------------------------------------
    # L1: URL registration
    # ------------------------------------------------------------------

    def test_urls_register_export_endpoints(self):
        """api/urls.py must register URL patterns for the export endpoints."""
        content = self._read("api", "urls.py")
        patterns = [r"export", r"Export"]
        assert any(
            re.search(p, content) for p in patterns
        ), "api/urls.py does not register any export-related URL patterns"

    # ------------------------------------------------------------------
    # L2: Input validation
    # ------------------------------------------------------------------

    def test_views_validate_date_range_parameters(self):
        """Export views must validate date range query parameters."""
        content = self._read("api", "views.py")
        date_patterns = [
            r"date",
            r"start_date",
            r"end_date",
            r"date_from",
            r"date_to",
            r"from_date",
            r"to_date",
            r"DateField",
            r"DateFilter",
            r"parse.*date",
            r"datetime",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in date_patterns
        ), "Export views do not appear to handle date range filtering parameters"

    # ------------------------------------------------------------------
    # L2: Django system check
    # ------------------------------------------------------------------

    def test_django_system_check_passes(self):
        """Django's manage.py check must pass after the modifications."""
        result = subprocess.run(
            ["python", "manage.py", "check", "--deploy"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
            env={
                **os.environ,
                "DJANGO_SETTINGS_MODULE": "babybuddy.settings.base",
                "SECRET_KEY": "test-secret-key-for-check",
            },
        )
        # --deploy may warn about settings; we only care about errors
        if result.returncode != 0:
            # Try without --deploy
            result2 = subprocess.run(
                ["python", "manage.py", "check"],
                cwd=self.REPO_DIR,
                capture_output=True,
                text=True,
                timeout=120,
            )
            assert (
                result2.returncode == 0
            ), f"Django system check failed:\n{result2.stdout[-2000:]}\n{result2.stderr[-2000:]}"

    # ------------------------------------------------------------------
    # L2: Python syntax for all modified files
    # ------------------------------------------------------------------

    def test_views_syntax_valid(self):
        """api/views.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "api/views.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error in api/views.py:\n{result.stderr}"

    def test_serializers_syntax_valid(self):
        """api/serializers.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "api/serializers.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            result.returncode == 0
        ), f"Syntax error in api/serializers.py:\n{result.stderr}"

    def test_urls_syntax_valid(self):
        """api/urls.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "api/urls.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error in api/urls.py:\n{result.stderr}"
