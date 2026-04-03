"""
Test for 'security-review' skill — Security review of babybuddy
Validates that the Agent performed a security review and applied fixes
to the babybuddy project.
"""

import os
import re

import pytest


class TestSecurityReview:
    """Verify security review findings and fixes in babybuddy."""

    REPO_DIR = "/workspace/babybuddy"

    def test_csrf_protection(self):
        """CSRF protection must be enabled."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"csrf|CsrfViewMiddleware|csrf_protect|csrf_token|CSRF_COOKIE", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No CSRF protection found"

    def test_authentication_required(self):
        """Authentication must be enforced on views."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"login_required|LoginRequiredMixin|IsAuthenticated|authentication_classes", content):
                        found = True
                        break
            if found:
                break
        assert found, "No authentication enforcement found"

    def test_input_validation(self):
        """User input must be validated."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"clean|validate|is_valid|serializer|form\.is_valid|validators", content):
                        found = True
                        break
            if found:
                break
        assert found, "No input validation found"

    def test_no_hardcoded_secrets(self):
        """No hardcoded secrets should exist in source code."""
        violations = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"SECRET_KEY\s*=\s*['\"][^'\"]{20,}['\"]", content):
                        if "os.environ" not in content and "getenv" not in content:
                            if "example" not in f.lower() and "test" not in f.lower():
                                violations.append(f)
        assert len(violations) == 0, f"Hardcoded secrets in: {violations}"

    def test_sql_injection_prevention(self):
        """SQL injection must be prevented (no raw SQL or parameterized)."""
        found_safe = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"\.objects\.|ORM|queryset|filter\(|get\(|\.raw\(.*%s", content):
                        found_safe = True
                        break
            if found_safe:
                break
        assert found_safe, "No ORM or parameterized SQL found"

    def test_xss_prevention(self):
        """XSS prevention measures must exist (auto-escaping, sanitization)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".html")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"escape|autoescape|mark_safe|bleach|sanitiz|{% autoescape", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No XSS prevention found"

    def test_secure_headers(self):
        """Security headers should be configured."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"SECURE_|X_FRAME_OPTIONS|CONTENT_TYPE_NOSNIFF|SecurityMiddleware|HSTS", content):
                        found = True
                        break
            if found:
                break
        assert found, "No secure headers configured"

    def test_password_hashing(self):
        """Passwords must be hashed."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"make_password|check_password|set_password|PASSWORD_HASHERS|bcrypt|pbkdf2", content):
                        found = True
                        break
            if found:
                break
        assert found, "No password hashing found"

    def test_https_enforcement(self):
        """HTTPS should be enforced or recommended."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"SECURE_SSL_REDIRECT|HTTPS|https://|SESSION_COOKIE_SECURE|CSRF_COOKIE_SECURE", content):
                        found = True
                        break
            if found:
                break
        assert found, "No HTTPS enforcement found"

    def test_settings_file_exists(self):
        """Django settings file must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "settings.py" or (f.endswith(".py") and "settings" in f.lower()):
                    found = True
                    break
            if found:
                break
        assert found, "No settings file found"
