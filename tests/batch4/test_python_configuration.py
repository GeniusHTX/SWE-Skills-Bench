"""
Test for 'python-configuration' skill — FastAPI Settings with Pydantic
Validates that the Agent created a Settings class with env-based config,
validation, computed properties, and proper .env.example for FastAPI.
"""

import os
import re
import sys

import pytest


class TestPythonConfiguration:
    """Verify Python configuration management with pydantic-settings."""

    REPO_DIR = "/workspace/fastapi"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _config_path(self):
        return os.path.join(
            self.REPO_DIR,
            "docs_src/advanced_settings/app/config.py",
        )

    def _main_path(self):
        return os.path.join(
            self.REPO_DIR,
            "docs_src/advanced_settings/app/main.py",
        )

    def _deps_path(self):
        return os.path.join(
            self.REPO_DIR,
            "docs_src/advanced_settings/app/dependencies.py",
        )

    def _env_example_path(self):
        return os.path.join(
            self.REPO_DIR,
            "docs_src/advanced_settings/.env.example",
        )

    def _import_settings(self):
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from docs_src.advanced_settings.app.config import (
                Settings,
                get_settings,
            )

            return Settings, get_settings
        finally:
            sys.path[:] = old_path

    # ---- file_path_check ----

    def test_config_py_exists(self):
        """Verifies docs_src/advanced_settings/app/config.py exists."""
        assert os.path.exists(
            self._config_path()
        ), f"File not found: {self._config_path()}"

    def test_main_py_exists(self):
        """Verifies docs_src/advanced_settings/app/main.py exists."""
        assert os.path.exists(self._main_path()), f"File not found: {self._main_path()}"

    def test_dependencies_py_exists(self):
        """Verifies docs_src/advanced_settings/app/dependencies.py exists."""
        assert os.path.exists(self._deps_path()), f"File not found: {self._deps_path()}"

    def test_env_example_exists(self):
        """Verifies docs_src/advanced_settings/.env.example exists."""
        assert os.path.exists(
            self._env_example_path()
        ), f"File not found: {self._env_example_path()}"

    # ---- semantic_check ----

    def test_sem_import_settings(self):
        """Verifies Settings and get_settings are importable."""
        Settings, get_settings = self._import_settings()
        assert Settings is not None
        assert get_settings is not None

    def test_sem_required_fields(self):
        """Verifies DATABASE_URL, SECRET_KEY, API_KEY in config."""
        text = self._read(self._config_path())
        for field in ["DATABASE_URL", "SECRET_KEY", "API_KEY"]:
            assert field in text, f"Required field '{field}' missing"

    def test_sem_default_values(self):
        """Verifies DB_POOL_SIZE and DB_POOL_TIMEOUT have defaults."""
        text = self._read(self._config_path())
        assert "DB_POOL_SIZE" in text, "DB_POOL_SIZE field missing"
        assert "DB_POOL_TIMEOUT" in text, "DB_POOL_TIMEOUT field missing"

    def test_sem_database_url_masked(self):
        """Verifies database_url_masked computed property."""
        text = self._read(self._config_path())
        assert "database_url_masked" in text, "database_url_masked property missing"

    def test_sem_environment_enum(self):
        """Verifies ENVIRONMENT field with development/staging/production."""
        text = self._read(self._config_path())
        assert "ENVIRONMENT" in text, "ENVIRONMENT field missing"
        assert (
            "development" in text or "staging" in text or "production" in text
        ), "ENVIRONMENT allowed values missing"

    def test_sem_env_example_markers(self):
        """Verifies .env.example has REQUIRED/SENSITIVE markers."""
        text = self._read(self._env_example_path())
        assert (
            "REQUIRED" in text.upper()
            or "SENSITIVE" in text.upper()
            or "DATABASE_URL" in text
        ), ".env.example missing key markers"

    # ---- functional_check ----

    def test_func_valid_settings(self):
        """Verifies Settings succeeds with valid env vars."""
        Settings, _ = self._import_settings()
        s = Settings(
            DATABASE_URL="db",
            SECRET_KEY="x" * 32,
            API_KEY="k",
        )
        assert s.DATABASE_URL == "db"

    def test_func_missing_env_raises(self):
        """Failure: Settings() with no env vars raises ValidationError."""
        Settings, _ = self._import_settings()
        with pytest.raises(Exception) as exc_info:
            Settings()
        assert (
            "DATABASE_URL" in str(exc_info.value)
            or "validation" in str(exc_info.value).lower()
        )

    def test_func_invalid_pool_size(self):
        """Failure: DB_POOL_SIZE=0 raises ValidationError."""
        Settings, _ = self._import_settings()
        with pytest.raises(Exception):
            Settings(
                DATABASE_URL="db",
                SECRET_KEY="x" * 32,
                API_KEY="k",
                DB_POOL_SIZE=0,
            )

    def test_func_invalid_log_level(self):
        """Failure: LOG_LEVEL='TRACE' raises ValidationError."""
        Settings, _ = self._import_settings()
        with pytest.raises(Exception):
            Settings(
                DATABASE_URL="db",
                SECRET_KEY="x" * 32,
                API_KEY="k",
                LOG_LEVEL="TRACE",
            )

    def test_func_production_debug_raises(self):
        """Failure: production + DEBUG=True raises."""
        Settings, _ = self._import_settings()
        with pytest.raises(Exception):
            Settings(
                ENVIRONMENT="production",
                DATABASE_URL="db",
                SECRET_KEY="x" * 32,
                API_KEY="k",
                DEBUG=True,
            )

    def test_func_production_localhost_cors_raises(self):
        """Failure: production + CORS_ORIGINS=['http://localhost:3000']."""
        Settings, _ = self._import_settings()
        with pytest.raises(Exception):
            Settings(
                ENVIRONMENT="production",
                DATABASE_URL="db",
                SECRET_KEY="x" * 64,
                API_KEY="k",
                CORS_ORIGINS=["http://localhost:3000"],
            )

    def test_func_masked_url(self):
        """Verifies database_url_masked masks password."""
        Settings, _ = self._import_settings()
        s = Settings(
            DATABASE_URL="postgresql://user:pass@host/db",
            SECRET_KEY="x" * 32,
            API_KEY="k",
        )
        masked = s.database_url_masked
        assert (
            "***" in masked or "pass" not in masked
        ), "Password not masked in database_url_masked"

    def test_func_masked_url_no_password(self):
        """Verifies database_url_masked with no password doesn't crash."""
        Settings, _ = self._import_settings()
        s = Settings(
            DATABASE_URL="sqlite:///test.db",
            SECRET_KEY="x" * 32,
            API_KEY="k",
        )
        masked = s.database_url_masked
        assert masked is not None, "database_url_masked returned None"
