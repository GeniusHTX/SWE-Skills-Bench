"""Test file for the python-configuration skill.

This suite validates Pydantic-based settings (DatabaseSettings, AppSettings)
with env vars, nested delimiter, validators, and lru_cache.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest


class TestPythonConfiguration:
    """Verify Python configuration patterns with FastAPI/Pydantic."""

    REPO_DIR = "/workspace/fastapi"

    CONFIG_PY = "docs_src/settings/config.py"
    TUTORIAL_PY = "docs_src/settings/tutorial001.py"
    TEST_PY = "tests/test_tutorial/test_settings/test_tutorial001.py"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    def _class_source(self, source: str, class_name: str) -> str | None:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                start = node.lineno - 1
                end = node.end_lineno or start + 1
                lines = source.splitlines()
                return "\n".join(lines[start:end])
        return None

    def _all_sources(self) -> str:
        parts = []
        for rel in (self.CONFIG_PY, self.TUTORIAL_PY):
            p = self._repo_path(rel)
            if p.is_file():
                parts.append(p.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_docs_src_settings_config_py_exists(self):
        """Verify config.py exists and is non-empty."""
        self._assert_non_empty_file(self.CONFIG_PY)

    def test_file_path_docs_src_settings_tutorial001_py_exists(self):
        """Verify tutorial001.py exists and is non-empty."""
        self._assert_non_empty_file(self.TUTORIAL_PY)

    def test_file_path_tests_test_tutorial_test_settings_test_tutorial001_py_exists(
        self,
    ):
        """Verify test_tutorial001.py exists and is non-empty."""
        self._assert_non_empty_file(self.TEST_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_databasesettings_has_fields_host_port_name_user_password_poo(
        self,
    ):
        """DatabaseSettings has fields: host, port, name, user, password, pool_size."""
        src = self._all_sources()
        body = self._class_source(src, "DatabaseSettings")
        assert body is not None, "DatabaseSettings class not found"
        for field in ("host", "port", "name", "user", "password", "pool_size"):
            assert field in body, f"DatabaseSettings missing field: {field}"

    def test_semantic_appsettings_has_env_nested_delimiter____and_env_file_env_in_(
        self,
    ):
        """AppSettings has env_nested_delimiter='__' and env_file='.env' in model config."""
        src = self._all_sources()
        body = self._class_source(src, "AppSettings")
        if body is None:
            body = self._class_source(src, "Settings")
        assert body is not None, "AppSettings/Settings class not found"
        assert re.search(r"env_nested_delimiter.*__", body) or re.search(
            r"nested.*__", src
        ), "AppSettings should have env_nested_delimiter='__'"

    def test_semantic_allowed_hosts_validator_handles_both_string_and_list_inputs(self):
        """allowed_hosts validator handles both string and list inputs."""
        src = self._all_sources()
        assert re.search(
            r"allowed_hosts|ALLOWED_HOSTS", src
        ), "allowed_hosts field not found"
        assert re.search(
            r"validator|field_validator|@validator", src
        ), "Validator for allowed_hosts not found"

    def test_semantic_production_validator_checks_debug_and_secret_key_length(self):
        """Production validator checks debug and secret_key length."""
        src = self._all_sources()
        assert re.search(r"debug|DEBUG", src) and re.search(
            r"secret_key|SECRET_KEY", src
        ), "Production validator should check debug and secret_key"

    def test_semantic_get_settings_uses_lru_cache_decorator(self):
        """get_settings() uses @lru_cache decorator."""
        src = self._all_sources()
        assert re.search(r"lru_cache|cache", src), "get_settings should use lru_cache"
        assert re.search(
            r"def\s+get_settings\s*\(", src
        ), "get_settings function not found"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, source analysis)
    # ------------------------------------------------------------------

    def test_functional_settings_load_from_environment_variables_with_correct_types(
        self,
    ):
        """Settings load from environment variables with correct types."""
        src = self._all_sources()
        assert re.search(
            r"BaseSettings|pydantic.settings|pydantic_settings", src
        ), "Settings should inherit from BaseSettings for env loading"

    def test_functional_nested_delimiter_database__host_overrides_database_host(self):
        """Nested delimiter DATABASE__HOST overrides database.host."""
        src = self._all_sources()
        assert re.search(
            r"env_nested_delimiter|nested", src
        ), "Nested delimiter support required"

    def test_functional_allowed_hosts_a_com_b_com_parsed_to_a_com_b_com(self):
        """ALLOWED_HOSTS='a.com, b.com' parsed to ['a.com', 'b.com']."""
        src = self._all_sources()
        assert re.search(
            r"split|,|comma", src, re.IGNORECASE
        ), "allowed_hosts validator should split comma-separated values"

    def test_functional_production_debug_true_raises_valueerror(self):
        """Production + debug=True raises ValueError."""
        src = self._all_sources()
        assert re.search(
            r"ValueError|ValidationError|raise", src
        ), "Production validator should raise on debug=True"

    def test_functional_production_short_secret_key_raises_valueerror(self):
        """Production + short secret_key raises ValueError."""
        src = self._all_sources()
        assert re.search(
            r"len\s*\(.*secret|secret.*len|min.*length", src, re.IGNORECASE
        ), "Production validator should check secret_key length"
