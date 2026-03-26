"""
Test for 'python-configuration' skill — Python Configuration Management
Validates that the Agent implemented a type-safe pydantic-settings tutorial
for FastAPI with environment variable reading, validation, and sensible defaults.
"""

import os
import re
import subprocess

import pytest

from _dependency_utils import ensure_python_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_python_dependencies(TestPythonConfiguration.REPO_DIR)
    # Ensure pydantic-settings is available
    subprocess.run(
        ["python", "-m", "pip", "install", "-q", "pydantic-settings", "pydantic"],
        cwd=TestPythonConfiguration.REPO_DIR,
        capture_output=True,
        timeout=120,
    )


class TestPythonConfiguration:
    """Verify type-safe configuration management tutorial for FastAPI."""

    REPO_DIR = "/workspace/fastapi"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence and syntax
    # ------------------------------------------------------------------

    def test_tutorial_file_exists(self):
        """docs_src/settings/tutorial001.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "docs_src", "settings", "tutorial001.py")
        assert os.path.isfile(fpath), "docs_src/settings/tutorial001.py not found"

    def test_tutorial_compiles(self):
        """tutorial001.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "docs_src/settings/tutorial001.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            result.returncode == 0
        ), f"Syntax error in tutorial001.py:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L1: Settings class structure
    # ------------------------------------------------------------------

    def test_defines_settings_class(self):
        """Tutorial must define a Settings class."""
        content = self._read("docs_src", "settings", "tutorial001.py")
        assert re.search(
            r"class\s+\w*Settings", content
        ), "No Settings class found in tutorial001.py"

    def test_settings_inherits_from_base_settings(self):
        """Settings class must inherit from pydantic BaseSettings."""
        content = self._read("docs_src", "settings", "tutorial001.py")
        patterns = [
            r"class\s+\w*Settings\s*\(\s*\w*BaseSettings",
            r"from\s+pydantic_settings\s+import\s+BaseSettings",
            r"from\s+pydantic\s+import\s+BaseSettings",
            r"pydantic_settings\.BaseSettings",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Settings class does not inherit from pydantic BaseSettings"

    # ------------------------------------------------------------------
    # L1: Required fields
    # ------------------------------------------------------------------

    def test_has_database_url_field(self):
        """Settings must include a database connection string field."""
        content = self._read("docs_src", "settings", "tutorial001.py")
        patterns = [
            r"database_url",
            r"db_url",
            r"database_uri",
            r"db_uri",
            r"DATABASE_URL",
            r"SQLALCHEMY_DATABASE",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Settings missing database URL/URI field"

    def test_has_debug_mode_field(self):
        """Settings must include a debug mode toggle field."""
        content = self._read("docs_src", "settings", "tutorial001.py")
        assert re.search(
            r"debug", content, re.IGNORECASE
        ), "Settings missing debug mode field"

    def test_has_host_and_port_fields(self):
        """Settings must include server host and port fields."""
        content = self._read("docs_src", "settings", "tutorial001.py")
        has_host = bool(re.search(r"host", content, re.IGNORECASE))
        has_port = bool(re.search(r"port", content, re.IGNORECASE))
        assert (
            has_host and has_port
        ), f"Settings missing host (found={has_host}) or port (found={has_port})"

    def test_has_api_key_field(self):
        """Settings must include an API key field (read from env, not hardcoded)."""
        content = self._read("docs_src", "settings", "tutorial001.py")
        patterns = [r"api_key", r"secret_key", r"API_KEY", r"SECRET_KEY"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Settings missing API key / secret key field"

    def test_has_cors_origins_field(self):
        """Settings must include an allowed CORS origins field."""
        content = self._read("docs_src", "settings", "tutorial001.py")
        patterns = [
            r"cors",
            r"allowed_origins",
            r"CORS_ORIGINS",
            r"origins",
            r"allow_origins",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Settings missing CORS origins field"

    # ------------------------------------------------------------------
    # L2: Type annotations and defaults
    # ------------------------------------------------------------------

    def test_fields_have_type_annotations(self):
        """Settings fields must have type annotations (str, int, bool, list, etc.)."""
        content = self._read("docs_src", "settings", "tutorial001.py")
        # Match field_name: Type patterns inside the Settings class
        annotations = re.findall(
            r"\w+\s*:\s*(?:str|int|bool|float|list|List|Optional|Set)", content
        )
        assert len(annotations) >= 3, (
            f"Only {len(annotations)} typed fields found — "
            f"Settings should have type annotations for all fields"
        )

    def test_sensitive_fields_not_hardcoded(self):
        """API keys and database URLs must not have hardcoded production values."""
        content = self._read("docs_src", "settings", "tutorial001.py")
        # Look for suspicious hardcoded values near sensitive field names
        bad_patterns = [
            r"api_key\s*[:=]\s*['\"](?!changeme|test|dummy|example|your)[a-zA-Z0-9]{20,}",
            r"database_url\s*[:=]\s*['\"](?:postgres|mysql|sqlite)://(?!localhost|example|test)",
        ]
        for pattern in bad_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            assert (
                not match
            ), f"Sensitive field appears to have a hardcoded production value: {match.group()}"

    # ------------------------------------------------------------------
    # L2: FastAPI integration
    # ------------------------------------------------------------------

    def test_fastapi_app_integration(self):
        """Tutorial must show how to use Settings with a FastAPI application."""
        content = self._read("docs_src", "settings", "tutorial001.py")
        patterns = [r"FastAPI", r"fastapi", r"app\s*=", r"Depends"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Tutorial does not demonstrate FastAPI integration"

    # ------------------------------------------------------------------
    # L2: Dynamic import/instantiation
    # ------------------------------------------------------------------

    def test_settings_instantiable_with_env_vars(self):
        """Settings class must be instantiable when required env vars are provided."""
        script = """
import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DATABASE_URL', 'sqlite:///test.db')
os.environ.setdefault('DB_URL', 'sqlite:///test.db')
os.environ.setdefault('DATABASE_URI', 'sqlite:///test.db')
os.environ.setdefault('API_KEY', 'test-api-key-12345')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-12345')
os.environ.setdefault('DEBUG', 'true')
os.environ.setdefault('HOST', '0.0.0.0')
os.environ.setdefault('PORT', '8000')
os.environ.setdefault('ALLOWED_ORIGINS', '["http://localhost"]')
os.environ.setdefault('CORS_ORIGINS', '["http://localhost"]')

import importlib.util
spec = importlib.util.spec_from_file_location(
    "tutorial001", "docs_src/settings/tutorial001.py")
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
    print('LOADED_OK')
except Exception as e:
    print(f'LOAD_ERROR={e}')

import inspect
for name, obj in inspect.getmembers(mod):
    if inspect.isclass(obj) and 'settings' in name.lower():
        try:
            instance = obj()
            print(f'INSTANTIATED={name}')
            break
        except Exception as e:
            print(f'INIT_ERROR={name}:{e}')
"""
        result = subprocess.run(
            ["python", "-c", script],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip()
        assert (
            "LOADED_OK" in output or "INSTANTIATED" in output
        ), f"Failed to load/instantiate Settings:\n{output}\n{result.stderr[-1000:]}"

    def test_env_file_support_mentioned(self):
        """Tutorial should demonstrate .env file support (env_file or dotenv)."""
        content = self._read("docs_src", "settings", "tutorial001.py")
        patterns = [r"env_file", r"\.env", r"dotenv", r"model_config"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Tutorial does not mention .env file support"
