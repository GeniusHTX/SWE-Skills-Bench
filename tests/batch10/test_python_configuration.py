"""
Test for 'python-configuration' skill — FastAPI configuration patterns
Validates that the Agent implemented Python configuration patterns
(settings, env vars, validation) in the FastAPI project.
"""

import os
import re

import pytest


class TestPythonConfiguration:
    """Verify Python configuration patterns in FastAPI."""

    REPO_DIR = "/workspace/fastapi"

    def test_settings_class_exists(self):
        """A Settings or Config class must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"class\s+(Settings|Config|AppConfig|AppSettings)\s*\(", content):
                        found = True
                        break
            if found:
                break
        assert found, "No Settings class found"

    def test_env_variable_loading(self):
        """Configuration must load from environment variables."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"os\.environ|os\.getenv|env_file|dotenv|Field\(.*env=", content):
                        found = True
                        break
            if found:
                break
        assert found, "No environment variable loading found"

    def test_pydantic_base_settings(self):
        """Settings should use pydantic BaseSettings or similar validation."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"BaseSettings|pydantic_settings|pydantic.*Settings", content):
                        found = True
                        break
            if found:
                break
        assert found, "No pydantic BaseSettings usage found"

    def test_default_values_defined(self):
        """Settings fields should have default values."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"(Settings|Config)", content):
                        if re.search(r"\w+\s*:\s*\w+\s*=\s*", content):
                            found = True
                            break
            if found:
                break
        assert found, "No default values in settings"

    def test_database_url_config(self):
        """Database URL or connection config should be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"database_url|DATABASE_URL|db_url|SQLALCHEMY_DATABASE|connection_string", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No database URL configuration found"

    def test_env_file_exists(self):
        """An .env or .env.example file should exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f in (".env", ".env.example", ".env.sample", ".env.template"):
                    found = True
                    break
            if found:
                break
        # Also check for env_file in code
        if not found:
            for root, dirs, files in os.walk(self.REPO_DIR):
                for f in files:
                    if f.endswith(".py"):
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            content = fh.read()
                        if re.search(r"env_file\s*=", content):
                            found = True
                            break
                if found:
                    break
        assert found, "No .env file or env_file reference found"

    def test_settings_dependency_injection(self):
        """Settings should be injected via FastAPI Depends or similar."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"Depends\(.*[Ss]ettings|get_settings|lru_cache.*settings", content):
                        found = True
                        break
            if found:
                break
        assert found, "No settings dependency injection found"

    def test_secret_handling(self):
        """Secrets should be handled securely."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Ss]ecret|SECRET_KEY|api_key|token|password", content):
                        found = True
                        break
            if found:
                break
        assert found, "No secret handling found"

    def test_validation_on_settings(self):
        """Settings should have validation (validators or Field constraints)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"validator|field_validator|model_validator|Field\(.*gt=|Field\(.*min_length|@validator", content):
                        found = True
                        break
            if found:
                break
        assert found, "No validation on settings"

    def test_multiple_environments(self):
        """Configuration should support multiple environments (dev/staging/prod)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".env", ".yaml", ".yml", ".toml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"development|staging|production|ENVIRONMENT|APP_ENV|ENV=", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No multi-environment configuration found"
