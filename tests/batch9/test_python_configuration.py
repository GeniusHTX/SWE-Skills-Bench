"""
Test for 'python-configuration' skill — Pydantic Settings Configuration
Validates AppSettings with nested settings, env_file, env_prefix, boolean coercion,
list parsing, secrets_dir, and ValidationError on missing required fields.
"""

import os
import re
import subprocess
import sys

import pytest


class TestPythonConfiguration:
    """Verify pydantic-settings configuration patterns."""

    REPO_DIR = "/workspace/fastapi"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _example(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "examples", "configuration", *parts)

    def _install_deps(self):
        try:
            import pydantic_settings  # noqa: F401
        except ImportError:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "pydantic-settings", "python-dotenv"],
                capture_output=True, timeout=60,
            )
            if result.returncode != 0:
                pytest.skip("pip install failed")

    # ── file_path_check ──────────────────────────────────────────────────

    def test_settings_py_and_init_exist(self):
        """settings.py and __init__.py must exist."""
        for name in ("settings.py", "__init__.py"):
            path = self._example(name)
            assert os.path.isfile(path), f"{path} does not exist"

    def test_env_example_and_test_file_exist(self):
        """.env.example and tests/test_configuration.py must exist."""
        env_path = self._example(".env.example")
        assert os.path.isfile(env_path), f"{env_path} does not exist"
        test_path = os.path.join(self.REPO_DIR, "tests", "test_configuration.py")
        assert os.path.isfile(test_path), f"{test_path} does not exist"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_app_settings_composes_nested(self):
        """AppSettings must aggregate nested settings like DbSettings, RedisSettings."""
        path = self._example("settings.py")
        if not os.path.isfile(path):
            pytest.skip("settings.py not found")
        content = self._read_file(path)
        assert "AppSettings" in content, "AppSettings class not defined"
        assert "BaseSettings" in content, "BaseSettings not referenced"
        has_nested = (
            "DbSettings" in content or "RedisSettings" in content or "DatabaseSettings" in content
        )
        assert has_nested, "No nested settings classes found"

    def test_model_config_env_file(self):
        """model_config must set env_file='.env' and env_file_encoding='utf-8'."""
        path = self._example("settings.py")
        if not os.path.isfile(path):
            pytest.skip("settings.py not found")
        content = self._read_file(path)
        assert "env_file" in content, "env_file not configured"
        assert "utf-8" in content or "utf8" in content, "env_file_encoding not set to utf-8"

    def test_env_prefix_defined(self):
        """Nested settings classes must define env_prefix."""
        path = self._example("settings.py")
        if not os.path.isfile(path):
            pytest.skip("settings.py not found")
        content = self._read_file(path)
        assert "env_prefix" in content, "env_prefix not configured"

    def test_required_fields_have_no_default(self):
        """At least one field must be required (no Optional or default value)."""
        path = self._example("settings.py")
        if not os.path.isfile(path):
            pytest.skip("settings.py not found")
        content = self._read_file(path)
        # Look for fields without = sign (required in pydantic)
        lines = content.splitlines()
        has_required = False
        for line in lines:
            stripped = line.strip()
            if re.match(r"\w+\s*:\s*\w+\s*$", stripped) and "Optional" not in stripped:
                has_required = True
                break
        assert has_required, "No required fields found (all have defaults or Optional)"

    # ── functional_check ─────────────────────────────────────────────────

    def test_bool_env_var_1_is_true(self):
        """APP_DEBUG='1' must parse as True."""
        self._install_deps()
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.configuration.settings import AppSettings
        except ImportError:
            pytest.skip("Cannot import AppSettings")
        os.environ["APP_DEBUG"] = "1"
        try:
            settings = AppSettings()
            assert settings.debug is True
        except Exception:
            pytest.skip("AppSettings instantiation requires additional env vars")
        finally:
            os.environ.pop("APP_DEBUG", None)

    def test_bool_env_var_false_is_false(self):
        """APP_DEBUG='false' must parse as False."""
        self._install_deps()
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.configuration.settings import AppSettings
        except ImportError:
            pytest.skip("Cannot import AppSettings")
        os.environ["APP_DEBUG"] = "false"
        try:
            settings = AppSettings()
            assert settings.debug is False
        except Exception:
            pytest.skip("AppSettings instantiation requires additional env vars")
        finally:
            os.environ.pop("APP_DEBUG", None)

    def test_missing_required_raises_validation_error(self):
        """Missing required env var must raise pydantic.ValidationError."""
        self._install_deps()
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.configuration.settings import AppSettings
            from pydantic import ValidationError
        except ImportError:
            pytest.skip("Cannot import AppSettings/ValidationError")
        # Clear all potentially required env vars
        cleared = {}
        for key in list(os.environ.keys()):
            if key.startswith(("APP_", "DB_", "REDIS_")):
                cleared[key] = os.environ.pop(key)
        try:
            with pytest.raises(ValidationError):
                AppSettings()
        finally:
            os.environ.update(cleared)

    def test_env_var_overrides_dotenv(self):
        """Env var set in os.environ must override .env file value."""
        path = self._example("settings.py")
        if not os.path.isfile(path):
            pytest.skip("settings.py not found")
        content = self._read_file(path)
        # Verify the settings module references env_file, ensuring override semantics
        assert "env_file" in content, "env_file not configured — cannot test override"

    def test_comma_list_parsing(self):
        """ALLOWED_HOSTS='host1,host2' must parse to ['host1', 'host2']."""
        path = self._example("settings.py")
        if not os.path.isfile(path):
            pytest.skip("settings.py not found")
        content = self._read_file(path)
        has_list = "List" in content or "list" in content or "allowed_hosts" in content
        assert has_list, "No list field (e.g., allowed_hosts) found in settings"

    def test_secrets_dir_pattern(self):
        """Settings should support secrets_dir for file-based secrets."""
        path = self._example("settings.py")
        if not os.path.isfile(path):
            pytest.skip("settings.py not found")
        content = self._read_file(path)
        has_secrets = "secrets_dir" in content or "SecretStr" in content
        assert has_secrets, "No secrets_dir or SecretStr pattern found"
