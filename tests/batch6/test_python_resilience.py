"""
Tests for 'python-resilience' skill.
Generated from benchmark case definitions for python-resilience.
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


class TestPythonResilience:
    """Verify the python-resilience skill output."""

    REPO_DIR = '/workspace/httpx'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestPythonResilience.REPO_DIR, rel)

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

    def test_resilience_module_exists(self):
        """Verify ResilientTransport module exists"""
        _p = self._repo_path('httpx/_resilience.py')
        assert os.path.isfile(_p), f'Missing file: httpx/_resilience.py'
        py_compile.compile(_p, doraise=True)

    def test_test_resilience_exists(self):
        """Verify test file exists"""
        _p = self._repo_path('tests/test_resilience.py')
        assert os.path.isfile(_p), f'Missing file: tests/test_resilience.py'
        py_compile.compile(_p, doraise=True)

    # ── semantic_check (static) ────────────────────────────────────────

    def test_resilient_transport_class_shape(self):
        """Verify ResilientTransport class with correct __init__ params"""
        _p = self._repo_path('httpx/_resilience.py')
        assert os.path.exists(_p), f'Missing: httpx/_resilience.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'class ResilientTransport' in _all, 'Missing: class ResilientTransport'
        assert 'max_retries' in _all, 'Missing: max_retries'
        assert 'backoff_base' in _all, 'Missing: backoff_base'
        assert 'backoff_max' in _all, 'Missing: backoff_max'
        assert 'backoff_jitter' in _all, 'Missing: backoff_jitter'
        assert 'failure_threshold' in _all, 'Missing: failure_threshold'
        assert 'recovery_timeout' in _all, 'Missing: recovery_timeout'
        assert 'success_threshold' in _all, 'Missing: success_threshold'

    def test_circuit_breaker_error_defined(self):
        """Verify CircuitBreakerOpenError inherits from httpx.TransportError"""
        _p = self._repo_path('httpx/_resilience.py')
        assert os.path.exists(_p), f'Missing: httpx/_resilience.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'CircuitBreakerOpenError' in _all, 'Missing: CircuitBreakerOpenError'
        assert 'TransportError' in _all, 'Missing: TransportError'

    def test_circuit_states_defined(self):
        """Verify CLOSED/OPEN/HALF_OPEN states defined"""
        _p = self._repo_path('httpx/_resilience.py')
        assert os.path.exists(_p), f'Missing: httpx/_resilience.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'CLOSED' in _all, 'Missing: CLOSED'
        assert 'OPEN' in _all, 'Missing: OPEN'
        assert 'HALF_OPEN' in _all, 'Missing: HALF_OPEN'

    # ── functional_check ────────────────────────────────────────

    def test_retry_transient_then_success(self):
        """Verify 503x3 then 200 succeeds with total_retries=3"""
        self._ensure_setup('test_retry_transient_then_success', ['pip install httpx pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_resilience.py', '-v', '-k', 'test_retry_success_after_transient'], timeout=120)
        assert result.returncode == 0, (
            f'test_retry_transient_then_success failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_max_retries_exhausted(self):
        """Verify always-503 with max_retries=3 raises after 4 attempts"""
        self._ensure_setup('test_max_retries_exhausted', ['pip install httpx pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_resilience.py', '-v', '-k', 'test_retries_exhausted'], timeout=120)
        assert result.returncode == 0, (
            f'test_max_retries_exhausted failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_401_no_retry(self):
        """Verify HTTP 401 propagates immediately without retry"""
        self._ensure_setup('test_401_no_retry', ['pip install httpx pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_resilience.py', '-v', '-k', 'test_401_no_retry'], timeout=120)
        assert result.returncode == 0, (
            f'test_401_no_retry failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_circuit_opens_after_failures(self):
        """Verify circuit opens after failure_threshold consecutive failures"""
        self._ensure_setup('test_circuit_opens_after_failures', ['pip install httpx pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_resilience.py', '-v', '-k', 'test_circuit_opens'], timeout=120)
        assert result.returncode == 0, (
            f'test_circuit_opens_after_failures failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_circuit_half_open_recovery(self):
        """Verify OPEN→HALF_OPEN→CLOSED recovery flow"""
        self._ensure_setup('test_circuit_half_open_recovery', ['pip install httpx pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_resilience.py', '-v', '-k', 'test_half_open_recovery'], timeout=120)
        assert result.returncode == 0, (
            f'test_circuit_half_open_recovery failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_max_retries_zero_disables(self):
        """Verify max_retries=0 disables retries entirely"""
        self._ensure_setup('test_max_retries_zero_disables', ['pip install httpx pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_resilience.py', '-v', '-k', 'test_max_retries_zero'], timeout=120)
        assert result.returncode == 0, (
            f'test_max_retries_zero_disables failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_retry_after_header_honored(self):
        """Verify 429 with Retry-After header overrides backoff"""
        self._ensure_setup('test_retry_after_header_honored', ['pip install httpx pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_resilience.py', '-v', '-k', 'test_retry_after_header'], timeout=120)
        assert result.returncode == 0, (
            f'test_retry_after_header_honored failed (exit {result.returncode})\n' + result.stderr[:500]
        )

