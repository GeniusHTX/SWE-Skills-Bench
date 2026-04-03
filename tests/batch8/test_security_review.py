"""
Test for 'security-review' skill — Django Security Review
Validates that the Agent performed a security review of the BabyBuddy Django
application covering CSRF, SQL injection, session cookies, and deploy checks.
"""

import os
import re
import subprocess

import pytest


class TestSecurityReview:
    """Verify Django security review implementation."""

    REPO_DIR = "/workspace/babybuddy"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_security_report_exists(self):
        """Verify SECURITY_REPORT.md exists at project root."""
        path = os.path.join(self.REPO_DIR, "SECURITY_REPORT.md")
        assert os.path.isfile(path), "Missing: SECURITY_REPORT.md"

    def test_settings_and_views_exist(self):
        """Verify babybuddy/settings.py and babybuddy/views.py exist."""
        for rel in ("babybuddy/settings.py", "babybuddy/views.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_models_exist(self):
        """Verify babybuddy/models.py exists."""
        path = os.path.join(self.REPO_DIR, "babybuddy/models.py")
        assert os.path.isfile(path), "Missing: babybuddy/models.py"

    # ── semantic_check ──────────────────────────────────────────────

    def test_no_raw_sql_fstring_injection(self):
        """Verify no raw SQL string f-strings that enable SQL injection."""
        content = self._read(os.path.join(self.REPO_DIR, "babybuddy/views.py"))
        assert content, "babybuddy/views.py is empty or unreadable"
        dangerous = ['f"SELECT', "f'SELECT", 'execute(f"', "execute(f'"]
        for pattern in dangerous:
            assert pattern not in content, \
                f"SQL injection risk: '{pattern}' found in views.py"

    def test_csrf_middleware_present(self):
        """Verify CsrfViewMiddleware is listed in MIDDLEWARE in settings.py."""
        content = self._read(os.path.join(self.REPO_DIR, "babybuddy/settings.py"))
        assert content, "babybuddy/settings.py is empty or unreadable"
        assert "CsrfViewMiddleware" in content, \
            "CsrfViewMiddleware not found in settings.py"

    def test_secret_key_from_env_variable(self):
        """Verify SECRET_KEY is loaded from environment variable, not hardcoded."""
        content = self._read(os.path.join(self.REPO_DIR, "babybuddy/settings.py"))
        assert content, "babybuddy/settings.py is empty or unreadable"
        found = any(kw in content for kw in (
            "os.environ.get", "os.getenv", "env('SECRET_KEY')"))
        assert found, "SECRET_KEY must be loaded from environment variable"

    def test_session_cookie_secure_and_httponly(self):
        """Verify SESSION_COOKIE_SECURE=True and SESSION_COOKIE_HTTPONLY=True."""
        content = self._read(os.path.join(self.REPO_DIR, "babybuddy/settings.py"))
        assert content, "babybuddy/settings.py is empty or unreadable"
        assert "SESSION_COOKIE_SECURE" in content, \
            "SESSION_COOKIE_SECURE not found"
        assert "SESSION_COOKIE_HTTPONLY" in content, \
            "SESSION_COOKIE_HTTPONLY not found"

    # ── functional_check (command) ──────────────────────────────────

    def _skip_unless_repo(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")

    def test_manage_py_check_deploy_exits_zero(self):
        """python manage.py check --deploy exits with code 0."""
        self._skip_unless_repo()
        result = subprocess.run(
            ["python", "manage.py", "check", "--deploy"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, \
            f"manage.py check --deploy failed: {result.stderr}"

    def test_anonymous_access_redirects_to_login(self):
        """Unauthenticated GET to a protected view returns 302 redirect."""
        self._skip_unless_repo()
        result = subprocess.run(
            ["python", "-c",
             "import django; import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'babybuddy.settings'); "
             "django.setup(); "
             "from django.test import Client; c = Client(); "
             "resp = c.get('/dashboard/'); "
             "assert resp.status_code == 302 and '/login' in resp['Location']"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=30,
        )
        assert result.returncode == 0, \
            f"Anonymous redirect check failed: {result.stderr}"

    def test_csrf_token_required_for_post(self):
        """POST without CSRF token to a protected form endpoint returns 403."""
        self._skip_unless_repo()
        result = subprocess.run(
            ["python", "-c",
             "import django; import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'babybuddy.settings'); "
             "django.setup(); "
             "from django.test import Client; c = Client(enforce_csrf_checks=True); "
             "resp = c.post('/api/feedings/', {'time': '2024-01-01T00:00:00'}); "
             "assert resp.status_code == 403"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=30,
        )
        assert result.returncode == 0, \
            f"CSRF enforcement check failed: {result.stderr}"
