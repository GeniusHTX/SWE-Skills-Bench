"""
Tests for 'python-configuration' skill.
Generated from benchmark case definitions for python-configuration.
"""

import ast
import base64
import glob
import json
import os
import py_compile
import re
import subprocess
import textwrap

import pytest

try:
    import yaml
except ModuleNotFoundError:
    yaml = None


class TestPythonConfiguration:
    """Verify the python-configuration skill output."""

    REPO_DIR = '/workspace/fastapi'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestPythonConfiguration.REPO_DIR, rel)

    @staticmethod
    def _safe_read(path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()

    @staticmethod
    def _load_yaml(path: str):
        if yaml is None:
            pytest.skip("PyYAML not available")
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return yaml.safe_load(fh)

    @staticmethod
    def _load_json(path: str):
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return json.load(fh)

    @classmethod
    def _run_in_repo(cls, script: str, timeout: int = 120) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python", "-c", textwrap.dedent(script)],
            cwd=cls.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    @classmethod
    def _run_cmd(cls, command, args=None, timeout=120):
        args = args or []
        if isinstance(command, str) and args:
            return subprocess.run(
                [command, *args],
                cwd=cls.REPO_DIR,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        return subprocess.run(
            command if isinstance(command, list) else command,
            cwd=cls.REPO_DIR,
            shell=isinstance(command, str),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    @classmethod
    def _ensure_setup(cls, label, setup_cmds, fallback):
        if not setup_cmds:
            return
        key = tuple(setup_cmds)
        if key in cls._SETUP_CACHE:
            ok, msg = cls._SETUP_CACHE[key]
            if ok:
                return
            if fallback == "skip_if_setup_fails":
                pytest.skip(f"{label} setup failed: {msg}")
            pytest.fail(f"{label} setup failed: {msg}")
        for cmd in setup_cmds:
            r = subprocess.run(cmd, cwd=cls.REPO_DIR, shell=True,
                               capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                msg = (r.stderr or r.stdout or 'failed').strip()
                cls._SETUP_CACHE[key] = (False, msg)
                if fallback == "skip_if_setup_fails":
                    pytest.skip(f"{label} setup failed: {msg}")
                pytest.fail(f"{label} setup failed: {msg}")
        cls._SETUP_CACHE[key] = (True, 'ok')


    # ── file_path_check (static) ────────────────────────────────────────

    def test_config_module_exists(self):
        """Verify settings configuration module exists"""
        _p = self._repo_path('app/config.py')
        assert os.path.isfile(_p), f'Missing file: app/config.py'
        py_compile.compile(_p, doraise=True)

    def test_env_file_exists(self):
        """Verify .env example or template file exists"""
        _p = self._repo_path('.env.example')
        assert os.path.isfile(_p), f'Missing file: .env.example'

    # ── semantic_check (static) ────────────────────────────────────────

    def test_settings_inherits_base_settings(self):
        """Verify Settings class inherits from BaseSettings"""
        _p = self._repo_path('app/config.py')
        assert os.path.exists(_p), f'Missing: app/config.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'BaseSettings' in _all, 'Missing: BaseSettings'
        assert 'class Settings' in _all, 'Missing: class Settings'

    def test_model_config_with_env_prefix(self):
        """Verify model_config or Config inner class sets env_prefix"""
        _p = self._repo_path('app/config.py')
        assert os.path.exists(_p), f'Missing: app/config.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'model_config' in _all, 'Missing: model_config'
        assert 'env_prefix' in _all, 'Missing: env_prefix'
        assert 'env_file' in _all, 'Missing: env_file'

    def test_nested_settings_class(self):
        """Verify nested settings with sub-prefix are defined"""
        _p = self._repo_path('app/config.py')
        assert os.path.exists(_p), f'Missing: app/config.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'DatabaseSettings' in _all, 'Missing: DatabaseSettings'
        assert 'RedisSettings' in _all, 'Missing: RedisSettings'
        assert 'env_prefix' in _all, 'Missing: env_prefix'

    def test_lru_cache_get_settings(self):
        """Verify get_settings function uses lru_cache decorator"""
        _p = self._repo_path('app/config.py')
        assert os.path.exists(_p), f'Missing: app/config.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'lru_cache' in _all, 'Missing: lru_cache'
        assert 'get_settings' in _all, 'Missing: get_settings'

    # ── functional_check ────────────────────────────────────────

    def test_env_var_loading(self):
        """Verify Settings loads values from environment variables"""
        self._ensure_setup('test_env_var_loading', ['pip install pydantic-settings fastapi'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import os; os.environ['APP_NAME']='TestApp'; os.environ['APP_DEBUG']='true'; from app.config import Settings; s=Settings(); assert s.app_name=='TestApp'; assert s.debug==True; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_env_var_loading failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_type_coercion_str_to_int(self):
        """Verify string env var coerced to int for port field"""
        self._ensure_setup('test_type_coercion_str_to_int', ['pip install pydantic-settings'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import os; os.environ['APP_PORT']='8080'; from app.config import Settings; s=Settings(); assert isinstance(s.port, int); assert s.port==8080; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_type_coercion_str_to_int failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_type_coercion_str_to_bool(self):
        """Verify string env var coerced to bool for debug field"""
        self._ensure_setup('test_type_coercion_str_to_bool', ['pip install pydantic-settings'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import os; os.environ['APP_DEBUG']='false'; from app.config import Settings; s=Settings(); assert s.debug is False; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_type_coercion_str_to_bool failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_missing_required_field_raises(self):
        """Verify missing required env var raises ValidationError"""
        self._ensure_setup('test_missing_required_field_raises', ['pip install pydantic-settings'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from pydantic import ValidationError\ntry:\n    from app.config import Settings; Settings()\n    assert False\nexcept ValidationError as e:\n    print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_missing_required_field_raises failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_get_settings_cached(self):
        """Verify get_settings returns same cached instance"""
        self._ensure_setup('test_get_settings_cached', ['pip install pydantic-settings'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from app.config import get_settings; s1=get_settings(); s2=get_settings(); assert s1 is s2; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_get_settings_cached failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_invalid_port_type_raises(self):
        """Verify non-numeric port string raises ValidationError"""
        self._ensure_setup('test_invalid_port_type_raises', ['pip install pydantic-settings'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import os; os.environ['APP_PORT']='not_a_number'\nfrom pydantic import ValidationError\ntry:\n    from app.config import Settings; Settings()\n    assert False\nexcept ValidationError:\n    print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_invalid_port_type_raises failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

