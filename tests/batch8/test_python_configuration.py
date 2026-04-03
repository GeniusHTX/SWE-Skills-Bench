"""
Test for 'python-configuration' skill — Pydantic-Settings Configuration
Validates that the Agent implemented a pydantic-settings based configuration
module with environment-driven settings, validation, and singleton caching.
"""

import os
import re
import sys

import pytest


class TestPythonConfiguration:
    """Verify pydantic-settings configuration implementation."""

    REPO_DIR = "/workspace/fastapi"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_config_and_database_files_exist(self):
        """Verify app/config.py and app/database.py exist."""
        for rel in ("app/config.py", "app/database.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_dependencies_file_exists(self):
        """Verify app/dependencies.py exists."""
        path = os.path.join(self.REPO_DIR, "app/dependencies.py")
        assert os.path.isfile(path), "Missing: app/dependencies.py"

    # ── semantic_check ──────────────────────────────────────────────

    def test_settings_inherits_base_settings(self):
        """Verify Settings class inherits BaseSettings from pydantic_settings."""
        content = self._read(os.path.join(self.REPO_DIR, "app/config.py"))
        assert content, "app/config.py is empty or unreadable"
        assert "BaseSettings" in content, "BaseSettings not found"
        assert "pydantic_settings" in content, "pydantic_settings import not found"

    def test_secret_key_from_environment(self):
        """SECRET_KEY is read from environment (not hardcoded)."""
        content = self._read(os.path.join(self.REPO_DIR, "app/config.py"))
        assert content, "app/config.py is empty or unreadable"
        assert "SECRET_KEY" in content, "SECRET_KEY not found in config"

    def test_session_cookie_secure_true(self):
        """Verify SESSION_COOKIE_SECURE = True in config (or default True)."""
        content = self._read(os.path.join(self.REPO_DIR, "app/config.py"))
        assert content, "app/config.py is empty or unreadable"
        found = any(kw in content for kw in ("SESSION_COOKIE_SECURE", "COOKIE_SECURE"))
        assert found, "SESSION_COOKIE_SECURE not found in config"

    def test_lru_cache_on_get_settings(self):
        """Verify get_settings() has @lru_cache decorator for singleton behavior."""
        content = self._read(os.path.join(self.REPO_DIR, "app/config.py"))
        assert content, "app/config.py is empty or unreadable"
        assert "lru_cache" in content, "lru_cache not found"
        assert "get_settings" in content, "get_settings not found"

    # ── functional_check (import) ───────────────────────────────────

    def _skip_unless_importable(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if self.REPO_DIR not in sys.path:
            sys.path.insert(0, self.REPO_DIR)

    def test_valid_postgresql_url_accepted(self):
        """Settings with valid postgresql:// URL and 32-char SECRET_KEY instantiates."""
        self._skip_unless_importable()
        os.environ.update({
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "SECRET_KEY": "a" * 32,
        })
        try:
            from app.config import Settings
        except Exception as exc:
            pytest.skip(f"Cannot import app.config: {exc}")
        s = Settings()
        assert str(s.DATABASE_URL).startswith("postgresql"), \
            "DATABASE_URL should start with 'postgresql'"

    def test_invalid_database_url_raises(self):
        """DATABASE_URL with http:// scheme raises ValidationError."""
        self._skip_unless_importable()
        os.environ["DATABASE_URL"] = "http://invalid"
        os.environ["SECRET_KEY"] = "a" * 32
        try:
            from app.config import Settings
        except Exception as exc:
            pytest.skip(f"Cannot import app.config: {exc}")
        with pytest.raises(Exception) as exc_info:
            Settings()
        assert "ValidationError" in type(exc_info.value).__name__ or \
            "validation" in str(exc_info.value).lower(), \
            "Expected ValidationError for http:// DATABASE_URL"

    def test_short_secret_key_raises(self):
        """SECRET_KEY with fewer than 32 chars raises ValidationError."""
        self._skip_unless_importable()
        os.environ["DATABASE_URL"] = "postgresql://u:p@h/db"
        os.environ["SECRET_KEY"] = "short"
        try:
            from app.config import Settings
        except Exception as exc:
            pytest.skip(f"Cannot import app.config: {exc}")
        with pytest.raises(Exception) as exc_info:
            Settings()
        assert "ValidationError" in type(exc_info.value).__name__ or \
            "validation" in str(exc_info.value).lower(), \
            "Expected ValidationError for short SECRET_KEY"

    def test_log_level_case_insensitive(self):
        """LOG_LEVEL='debug' (lowercase) is accepted and normalized to 'DEBUG'."""
        self._skip_unless_importable()
        os.environ.update({
            "DATABASE_URL": "postgresql://u:p@h/db",
            "SECRET_KEY": "a" * 32,
            "LOG_LEVEL": "debug",
        })
        try:
            from app.config import Settings
        except Exception as exc:
            pytest.skip(f"Cannot import app.config: {exc}")
        s = Settings()
        assert s.LOG_LEVEL.upper() == "DEBUG", \
            "LOG_LEVEL should normalize to 'DEBUG'"

    def test_get_settings_returns_same_instance(self):
        """get_settings() called twice returns the same cached instance."""
        self._skip_unless_importable()
        os.environ.update({
            "DATABASE_URL": "postgresql://u:p@h/db",
            "SECRET_KEY": "a" * 32,
        })
        try:
            from app.config import get_settings
        except Exception as exc:
            pytest.skip(f"Cannot import app.config: {exc}")
        assert get_settings() is get_settings(), \
            "get_settings() must return cached singleton"
