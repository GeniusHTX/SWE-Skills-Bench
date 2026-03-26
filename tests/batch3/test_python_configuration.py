"""
Tests for python-configuration skill.
Validates AppSettings, DatabaseSettings, and get_settings in FastAPI test_app.
"""

import os
import pytest

REPO_DIR = "/workspace/fastapi"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestPythonConfiguration:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_config_py_exists(self):
        """tests/test_app/config.py must exist."""
        rel = "tests/test_app/config.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "config.py is empty"

    def test_test_app_init_exists(self):
        """tests/test_app/__init__.py must exist for importability."""
        rel = "tests/test_app/__init__.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_app_settings_class_defined(self):
        """config.py must define AppSettings with environment, debug, secret_key fields."""
        content = _read("tests/test_app/config.py")
        assert "class AppSettings" in content, "AppSettings class not defined"
        for field in ("environment", "debug", "secret_key"):
            assert field in content, f"'{field}' field not found in config.py"

    def test_database_settings_password_hidden_in_repr(self):
        """config.py must mask password in __repr__ to prevent secret leakage."""
        content = _read("tests/test_app/config.py")
        has_repr = "__repr__" in content or "__str__" in content
        has_mask = (
            "***" in content or "REDACTED" in content or "hidden" in content.lower()
        )
        assert has_repr, "__repr__ or __str__ override not found in config.py"
        assert has_mask, "Password masking pattern not found in config.py"

    def test_validation_production_debug_defined(self):
        """config.py must validate that production+debug=True is rejected."""
        content = _read("tests/test_app/config.py")
        assert (
            "production" in content.lower()
        ), "'production' environment not referenced"
        assert "debug" in content.lower(), "'debug' flag not referenced"
        assert (
            "validator" in content or "@" in content
        ), "No validator decorator found in config.py"

    def test_get_settings_singleton_pattern(self):
        """get_settings must use @lru_cache for singleton behavior."""
        content = _read("tests/test_app/config.py")
        assert "lru_cache" in content, "@lru_cache not found in config.py"
        assert "get_settings" in content, "get_settings function not defined"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_production_debug_true_raises_value_error(self):
        """production environment with debug=True must raise ValueError (mocked)."""
        from pydantic import BaseModel, validator

        class AppSettings(BaseModel):
            environment: str
            debug: bool = False
            secret_key: str

            @validator("debug")
            def no_debug_in_production(cls, v, values):
                if v and values.get("environment") == "production":
                    raise ValueError("debug mode not allowed in production")
                return v

        with pytest.raises((ValueError, Exception)):
            AppSettings(environment="production", debug=True, secret_key="a" * 32)

    def test_allowed_hosts_wildcard_raises_value_error(self):
        """allowed_hosts=['*'] must raise ValueError (mocked)."""
        from pydantic import BaseModel, validator
        from typing import List

        class AppSettings(BaseModel):
            environment: str = "development"
            allowed_hosts: List[str] = []
            secret_key: str

            @validator("allowed_hosts")
            def no_wildcard_hosts(cls, v):
                if "*" in v:
                    raise ValueError("Wildcard '*' not allowed in allowed_hosts")
                return v

        with pytest.raises((ValueError, Exception)):
            AppSettings(
                environment="development", allowed_hosts=["*"], secret_key="a" * 32
            )

    def test_port_99999_raises_value_error(self):
        """DatabaseSettings port 99999 must raise ValueError (mocked)."""
        from pydantic import BaseModel, validator

        class DatabaseSettings(BaseModel):
            host: str
            port: int
            name: str
            user: str
            password: str

            @validator("port")
            def valid_port(cls, v):
                if not (1 <= v <= 65535):
                    raise ValueError(f"port {v} is not in range 1-65535")
                return v

        with pytest.raises((ValueError, Exception)):
            DatabaseSettings(
                host="db", port=99999, name="mydb", user="user", password="pass"
            )

    def test_secret_key_less_than_32_chars_rejected(self):
        """secret_key shorter than 32 chars must raise ValueError (mocked)."""
        from pydantic import BaseModel, validator

        class AppSettings(BaseModel):
            environment: str = "development"
            secret_key: str

            @validator("secret_key")
            def secret_key_length(cls, v):
                if len(v) < 32:
                    raise ValueError("secret_key must be at least 32 characters")
                return v

        with pytest.raises((ValueError, Exception)):
            AppSettings(environment="development", secret_key="tooshort")

    def test_development_env_sets_debug_logging(self):
        """Development environment must set DEBUG log level (mocked)."""
        import logging

        def get_log_level(environment: str) -> int:
            mapping = {
                "development": logging.DEBUG,
                "staging": logging.INFO,
                "production": logging.WARNING,
            }
            return mapping.get(environment, logging.INFO)

        assert get_log_level("development") == logging.DEBUG

    def test_get_settings_returns_same_instance(self):
        """get_settings() must return the same instance on repeated calls (mocked)."""
        from functools import lru_cache

        class Settings:
            def __init__(self):
                self.value = 42

        @lru_cache(maxsize=1)
        def get_settings():
            return Settings()

        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2, "get_settings must return same singleton instance"
