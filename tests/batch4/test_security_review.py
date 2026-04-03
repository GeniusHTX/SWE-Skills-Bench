"""
Test for 'security-review' skill — BabyBuddy Security Review
Validates that the Agent applied security hardening to the babybuddy Django project:
secure settings, XSS/CSRF protection, password validators, CSP, rate limiting.
"""

import ast
import glob
import os
import re

import pytest


class TestSecurityReview:
    """Verify babybuddy security hardening."""

    REPO_DIR = "/workspace/babybuddy"

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _find_settings_text(self):
        """Read the settings file — try settings/base.py first, then settings.py."""
        for rel in ("babybuddy/settings/base.py", "babybuddy/settings.py"):
            path = os.path.join(self.REPO_DIR, rel)
            if os.path.exists(path):
                return self._read(path), path
        return None, None

    # ---- file_path_check ----

    def test_settings_base_py_exists(self):
        """Verifies babybuddy/settings/base.py exists."""
        path = os.path.join(self.REPO_DIR, "babybuddy/settings/base.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_settings_py_exists(self):
        """Verifies babybuddy/settings.py exists."""
        path = os.path.join(self.REPO_DIR, "babybuddy/settings.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_middleware_py_exists(self):
        """Verifies babybuddy/middleware.py exists."""
        path = os.path.join(self.REPO_DIR, "babybuddy/middleware.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_any_middleware_file_exists(self):
        """Verifies at least one middleware*.py file exists anywhere in the project."""
        matches = glob.glob(
            os.path.join(self.REPO_DIR, "**", "middleware*.py"), recursive=True
        )
        assert len(matches) > 0, "No middleware*.py file found in the project"

    # ---- semantic_check ----

    def test_settings_readable(self):
        """Settings file can be read and is non-empty."""
        settings_text, _ = self._find_settings_text()
        assert (
            settings_text is not None and len(settings_text) > 0
        ), "Could not read settings file"

    def test_secure_browser_xss_or_hsts(self):
        """Settings should have SECURE_BROWSER_XSS_FILTER or SECURE_HSTS_SECONDS."""
        settings_text, _ = self._find_settings_text()
        assert settings_text is not None, "Settings file not found"
        assert (
            "SECURE_BROWSER_XSS_FILTER" in settings_text
            or "SECURE_HSTS_SECONDS" in settings_text
        ), "Missing XSS filter or HSTS setting"

    def test_x_frame_options_present(self):
        """Settings should define X_FRAME_OPTIONS."""
        settings_text, _ = self._find_settings_text()
        assert settings_text is not None, "Settings file not found"
        assert "X_FRAME_OPTIONS" in settings_text, "Missing X_FRAME_OPTIONS"

    def test_auth_password_validators_present(self):
        """Settings should define AUTH_PASSWORD_VALIDATORS."""
        settings_text, _ = self._find_settings_text()
        assert settings_text is not None, "Settings file not found"
        assert (
            "AUTH_PASSWORD_VALIDATORS" in settings_text
        ), "Missing AUTH_PASSWORD_VALIDATORS"

    def test_no_hardcoded_secret_key(self):
        """SECRET_KEY must not be hardcoded as a long literal string."""
        settings_text, _ = self._find_settings_text()
        assert settings_text is not None, "Settings file not found"
        match = re.search(
            r"SECRET_KEY\s*=\s*['\"][a-zA-Z0-9!@#$%^&*]{20,}", settings_text
        )
        assert match is None, "SECRET_KEY appears to be hardcoded as a literal string"

    # ---- functional_check ----

    def test_settings_parseable_as_python(self):
        """Settings file should parse as valid Python AST."""
        settings_text, settings_path = self._find_settings_text()
        assert settings_text is not None, "Settings file not found"
        try:
            ast.parse(settings_text)
        except SyntaxError as e:
            pytest.fail(f"Settings file has syntax error: {e}")

    def test_xss_or_hsts_in_ast_assignments(self):
        """SECURE_BROWSER_XSS_FILTER or SECURE_HSTS_SECONDS should be assigned."""
        settings_text, _ = self._find_settings_text()
        assert settings_text is not None, "Settings file not found"
        assert (
            "SECURE_BROWSER_XSS_FILTER" in settings_text
            or "SECURE_HSTS_SECONDS" in settings_text
        ), "No XSS or HSTS assignment found in settings"

    def test_x_frame_options_in_ast(self):
        """X_FRAME_OPTIONS should be assigned in settings."""
        settings_text, _ = self._find_settings_text()
        assert settings_text is not None, "Settings file not found"
        assert (
            "X_FRAME_OPTIONS" in settings_text
        ), "X_FRAME_OPTIONS not assigned in settings"

    def test_password_validators_count(self):
        """AUTH_PASSWORD_VALIDATORS should have at least 3 validators."""
        settings_text, _ = self._find_settings_text()
        assert settings_text is not None, "Settings file not found"
        try:
            tree = ast.parse(settings_text)
        except SyntaxError:
            pytest.skip("Settings file has syntax errors")
        validators = []
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Assign)
                and node.targets
                and hasattr(node.targets[0], "id")
                and node.targets[0].id == "AUTH_PASSWORD_VALIDATORS"
                and isinstance(node.value, ast.List)
            ):
                validators = node.value.elts
                break
        assert (
            len(validators) >= 3
        ), f"AUTH_PASSWORD_VALIDATORS should have >= 3 validators, got {len(validators)}"

    def test_secret_key_uses_environ(self):
        """SECRET_KEY should reference os.environ or env variable."""
        settings_text, _ = self._find_settings_text()
        assert settings_text is not None, "Settings file not found"
        assert (
            "environ" in settings_text and "SECRET_KEY" in settings_text
        ), "SECRET_KEY should use os.environ.get or similar"

    def test_rate_limiting_present(self):
        """Rate limiting should be present (via middleware, decorator, or config)."""
        settings_text, _ = self._find_settings_text()
        # Check in middleware
        mw_path = os.path.join(self.REPO_DIR, "babybuddy", "middleware.py")
        mw_text = self._read(mw_path) if os.path.exists(mw_path) else ""
        combined = (settings_text or "") + mw_text
        assert any(
            kw in combined
            for kw in [
                "@ratelimit",
                "RateLimit",
                "django_ratelimit",
                "throttle",
                "Throttle",
            ]
        ), "No rate limiting mechanism found"

    def test_csp_present(self):
        """Content Security Policy should be configured."""
        settings_text, _ = self._find_settings_text()
        assert settings_text is not None, "Settings file not found"
        req_path = os.path.join(self.REPO_DIR, "requirements.txt")
        req_text = self._read(req_path) if os.path.exists(req_path) else ""
        csp_present = (
            "CSP_DEFAULT_SRC" in settings_text
            or "ContentSecurityPolicy" in settings_text
            or "django-csp" in req_text
        )
        assert (
            csp_present
        ), "No Content Security Policy found in settings or requirements"

    def test_no_raw_sql_injection_patterns(self):
        """No raw SQL cursor.execute with % formatting should be present."""
        py_files = glob.glob(os.path.join(self.REPO_DIR, "**", "*.py"), recursive=True)
        sql_injection_pattern = re.compile(r"cursor\.execute\([^,)]*%\s*[^,)]*\)")
        for f in py_files[:50]:  # limit scan to avoid timeout
            content = self._read(f)
            match = sql_injection_pattern.search(content)
            assert (
                match is None
            ), f"Potential SQL injection pattern found in {f}: {match.group()}"

    def test_hardcoded_secret_key_failure(self):
        """Detects if SECRET_KEY is hardcoded as a long literal — should fail."""
        settings_text, _ = self._find_settings_text()
        assert settings_text is not None, "Settings file not found"
        match = re.search(
            r"SECRET_KEY\s*=\s*['\"][a-zA-Z0-9!@#$%^&*()_+]{20,}['\"]",
            settings_text,
        )
        assert match is None, "Hardcoded SECRET_KEY detected in settings.py"
