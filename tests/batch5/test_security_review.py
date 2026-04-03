"""
Test for 'security-review' skill — BabyBuddy Security Review
Validates SESSION_COOKIE_HTTPONLY, CsrfViewMiddleware, no |safe template
filter misuse, security middleware, and Django security settings.
"""

import os
import re

import pytest


class TestSecurityReview:
    """Verify security review findings in BabyBuddy."""

    REPO_DIR = "/workspace/babybuddy"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_settings_file_exists(self):
        """Verify Django settings file exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f == "settings.py" or (
                    f.endswith(".py") and "settings" in f.lower()
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No settings.py found"

    def test_template_files_exist(self):
        """Verify HTML template files exist."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".html"):
                    found = True
                    break
            if found:
                break
        assert found, "No HTML template files found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_session_cookie_httponly(self):
        """Verify SESSION_COOKIE_HTTPONLY = True."""
        settings_files = self._find_settings_files()
        for fpath in settings_files:
            content = self._read(fpath)
            if re.search(r"SESSION_COOKIE_HTTPONLY\s*=\s*True", content):
                return
        pytest.fail("SESSION_COOKIE_HTTPONLY = True not found")

    def test_csrf_middleware(self):
        """Verify CsrfViewMiddleware is in MIDDLEWARE."""
        settings_files = self._find_settings_files()
        for fpath in settings_files:
            content = self._read(fpath)
            if "CsrfViewMiddleware" in content:
                return
        pytest.fail("CsrfViewMiddleware not in MIDDLEWARE")

    def test_no_unsafe_template_filter(self):
        """Verify templates don't misuse |safe filter on user input."""
        violations = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".html"):
                    fpath = os.path.join(dirpath, f)
                    content = self._read(fpath)
                    # Flag direct user input with |safe (heuristic)
                    if re.search(r"\{\{.*user.*\|.*safe.*\}\}", content, re.IGNORECASE):
                        violations.append(os.path.basename(fpath))
        assert not violations, f"|safe on user input in: {violations[:5]}"

    def test_secure_cookie_settings(self):
        """Verify secure cookie settings."""
        settings_files = self._find_settings_files()
        for fpath in settings_files:
            content = self._read(fpath)
            if re.search(
                r"(SESSION_COOKIE_SECURE|CSRF_COOKIE_SECURE|SECURE_SSL_REDIRECT)",
                content,
            ):
                return
        pytest.fail("No secure cookie settings found")

    def test_security_middleware(self):
        """Verify SecurityMiddleware is configured."""
        settings_files = self._find_settings_files()
        for fpath in settings_files:
            content = self._read(fpath)
            if "SecurityMiddleware" in content:
                return
        pytest.fail("SecurityMiddleware not found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_settings_parseable(self):
        """Verify settings files are syntactically valid."""
        import ast

        settings_files = self._find_settings_files()
        for fpath in settings_files:
            content = self._read(fpath)
            try:
                ast.parse(content, filename=fpath)
            except SyntaxError as e:
                pytest.fail(f"SyntaxError in {os.path.basename(fpath)}: {e}")

    def test_debug_false_in_production(self):
        """Verify DEBUG is not hardcoded to True in base settings."""
        settings_files = self._find_settings_files()
        for fpath in settings_files:
            if "prod" in fpath.lower() or "base" in fpath.lower():
                content = self._read(fpath)
                if re.search(r"DEBUG\s*=\s*True", content):
                    pytest.fail(f"DEBUG = True in {os.path.basename(fpath)}")

    def test_allowed_hosts_configured(self):
        """Verify ALLOWED_HOSTS is configured."""
        settings_files = self._find_settings_files()
        for fpath in settings_files:
            content = self._read(fpath)
            if "ALLOWED_HOSTS" in content:
                return
        pytest.fail("No ALLOWED_HOSTS configuration found")

    def test_password_validators(self):
        """Verify AUTH_PASSWORD_VALIDATORS are configured."""
        settings_files = self._find_settings_files()
        for fpath in settings_files:
            content = self._read(fpath)
            if "AUTH_PASSWORD_VALIDATORS" in content:
                return
        pytest.fail("No AUTH_PASSWORD_VALIDATORS found")

    def test_no_hardcoded_secrets(self):
        """Verify no hardcoded SECRET_KEY in settings."""
        settings_files = self._find_settings_files()
        for fpath in settings_files:
            content = self._read(fpath)
            match = re.search(r"SECRET_KEY\s*=\s*['\"]([^'\"]+)['\"]", content)
            if match:
                key = match.group(1)
                # Allow if it references env or is a placeholder
                if not re.search(
                    r"(os\.environ|env\(|getenv|CHANGE_ME|xxx|placeholder)",
                    content[max(0, content.find(key) - 100) : content.find(key) + 100],
                    re.IGNORECASE,
                ):
                    pytest.fail(
                        f"Hardcoded SECRET_KEY found in {os.path.basename(fpath)}"
                    )

    def test_xss_protection_headers(self):
        """Verify XSS protection headers or CSP."""
        settings_files = self._find_settings_files()
        for fpath in settings_files:
            content = self._read(fpath)
            if re.search(
                r"(X_FRAME_OPTIONS|SECURE_BROWSER_XSS_FILTER|Content.?Security.?Policy|CSP)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.skip("No XSS header settings (may use defaults)")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_settings_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and "setting" in f.lower():
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
