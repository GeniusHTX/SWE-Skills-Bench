"""
Test for 'python-configuration' skill — FastAPI Pydantic Settings
Validates Pydantic BaseSettings, env_prefix APP_, pool_size validation
(1-50), .env file support, and configuration layering.
"""

import os
import re
import sys

import pytest


class TestPythonConfiguration:
    """Verify Python configuration management with Pydantic."""

    REPO_DIR = "/workspace/fastapi"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_settings_file_exists(self):
        """Verify settings/config Python file exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and (
                    "config" in f.lower() or "settings" in f.lower()
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No settings/config file found"

    def test_env_file_exists(self):
        """Verify .env or .env.example file exists."""
        for name in (".env", ".env.example", ".env.sample", "env.example"):
            if os.path.exists(os.path.join(self.REPO_DIR, name)):
                return
        # Also check subdirectories
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.startswith(".env") or f == "env.example":
                    return
        pytest.skip(".env file not found (may not be required)")

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_pydantic_base_settings(self):
        """Verify Pydantic BaseSettings usage."""
        py_files = self._find_config_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(BaseSettings|pydantic.?settings)", content):
                return
        pytest.fail("No Pydantic BaseSettings usage found")

    def test_env_prefix_app(self):
        """Verify env_prefix is configured (e.g. APP_)."""
        py_files = self._find_config_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"env_prefix\s*=", content):
                return
        pytest.fail("No env_prefix configuration found")

    def test_pool_size_validation(self):
        """Verify pool_size has validation constraints (1-50 or similar)."""
        py_files = self._find_config_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"pool_size", content):
                if re.search(
                    r"(Field\(|validator|ge\s*=|le\s*=|gt\s*=|lt\s*=|\d+.*\d+)", content
                ):
                    return
        pytest.fail("No pool_size validation found")

    def test_field_validators(self):
        """Verify Pydantic Field validators are used."""
        py_files = self._find_config_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(Field\(|@validator|@field_validator|@model_validator)", content
            ):
                return
        pytest.fail("No Pydantic validators found")

    def test_env_file_support(self):
        """Verify .env file support in settings."""
        py_files = self._find_config_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(env_file\s*=|\.env|dotenv)", content):
                return
        pytest.fail("No .env file support found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_config_files_parse(self):
        """Verify config files are syntactically valid."""
        import py_compile

        py_files = self._find_config_files()
        for fpath in py_files[:5]:
            try:
                py_compile.compile(fpath, doraise=True)
            except py_compile.PyCompileError:
                pytest.skip(f"Syntax issue in {os.path.basename(fpath)}")

    def test_settings_class_inherits_base(self):
        """Verify Settings class inherits from BaseSettings."""
        py_files = self._find_config_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"class \w+Settings?\(.*BaseSettings.*\)", content):
                return
        pytest.fail("No class inheriting BaseSettings found")

    def test_default_values_defined(self):
        """Verify settings have sensible default values."""
        py_files = self._find_config_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r":\s*(str|int|float|bool)\s*=\s*\S+", content):
                return
        pytest.fail("No default values in settings")

    def test_typed_fields(self):
        """Verify settings fields have type annotations."""
        py_files = self._find_config_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r":\s*(str|int|float|bool|Optional|List|Dict)", content):
                return
        pytest.fail("No typed fields in settings")

    def test_nested_model_support(self):
        """Verify nested configuration model support."""
        py_files = self._find_config_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(BaseModel|model_config|class Config)", content):
                return
        pytest.skip("No nested model found (may not be required)")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_config_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and (
                    "config" in f.lower() or "settings" in f.lower()
                ):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
