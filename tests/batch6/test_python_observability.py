"""
Tests for 'python-observability' skill.
Generated from benchmark case definitions for python-observability.
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


class TestPythonObservability:
    """Verify the python-observability skill output."""

    REPO_DIR = '/workspace/opentelemetry-python'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestPythonObservability.REPO_DIR, rel)

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

    def test_logging_config_exists(self):
        """Verify logging config module exists"""
        _p = self._repo_path('docs/examples/observability_demo/logging_config.py')
        assert os.path.isfile(_p), f'Missing file: docs/examples/observability_demo/logging_config.py'
        py_compile.compile(_p, doraise=True)

    def test_middleware_and_metrics_exist(self):
        """Verify middleware and metrics modules exist"""
        _p = self._repo_path('docs/examples/observability_demo/middleware.py')
        assert os.path.isfile(_p), f'Missing file: docs/examples/observability_demo/middleware.py'
        py_compile.compile(_p, doraise=True)
        _p = self._repo_path('docs/examples/observability_demo/metrics.py')
        assert os.path.isfile(_p), f'Missing file: docs/examples/observability_demo/metrics.py'
        py_compile.compile(_p, doraise=True)

    # ── semantic_check (static) ────────────────────────────────────────

    def test_structlog_json_renderer(self):
        """Verify structlog configured with JSONRenderer as last processor"""
        _p = self._repo_path('docs/examples/observability_demo/logging_config.py')
        assert os.path.exists(_p), f'Missing: docs/examples/observability_demo/logging_config.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'JSONRenderer' in _all, 'Missing: JSONRenderer'
        assert 'structlog.configure' in _all, 'Missing: structlog.configure'
        assert 'processors' in _all, 'Missing: processors'

    def test_tracer_provider_setup(self):
        """Verify TracerProvider initialized with batch span processor"""
        _p = self._repo_path('docs/examples/observability_demo/middleware.py')
        assert os.path.exists(_p), f'Missing: docs/examples/observability_demo/middleware.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'TracerProvider' in _all, 'Missing: TracerProvider'
        assert 'BatchSpanProcessor' in _all, 'Missing: BatchSpanProcessor'
        assert 'set_tracer_provider' in _all, 'Missing: set_tracer_provider'

    def test_trace_id_extraction_pattern(self):
        """Verify trace_id extracted from active span for log correlation"""
        _p = self._repo_path('docs/examples/observability_demo/middleware.py')
        assert os.path.exists(_p), f'Missing: docs/examples/observability_demo/middleware.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'get_current_span' in _all, 'Missing: get_current_span'
        assert 'trace_id' in _all, 'Missing: trace_id'
        assert 'span_id' in _all, 'Missing: span_id'

    def test_histogram_and_gauge_instruments(self):
        """Verify Histogram and Gauge metrics instruments created"""
        _p = self._repo_path('docs/examples/observability_demo/metrics.py')
        assert os.path.exists(_p), f'Missing: docs/examples/observability_demo/metrics.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'Histogram' in _all, 'Missing: Histogram'
        assert 'Gauge' in _all, 'Missing: Gauge'
        assert 'create_histogram' in _all, 'Missing: create_histogram'
        assert 'create_observable_gauge' in _all, 'Missing: create_observable_gauge'

    # ── functional_check ────────────────────────────────────────

    def test_json_log_output(self):
        """Verify log output is valid JSON with trace_id field"""
        self._ensure_setup('test_json_log_output', ['pip install opentelemetry-sdk opentelemetry-api structlog fastapi'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from docs.examples.observability_demo.logging_config import configure_logging; import structlog, io, json; configure_logging(); logger=structlog.get_logger(); import sys; logger.info('test_event'); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_json_log_output failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_request_histogram_exists(self):
        """Verify request histogram instrument can be obtained"""
        self._ensure_setup('test_request_histogram_exists', ['pip install opentelemetry-sdk opentelemetry-api'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from docs.examples.observability_demo.metrics import get_request_histogram; h=get_request_histogram(); assert h is not None; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_request_histogram_exists failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_500_sets_error_span_status(self):
        """Verify 500 error response sets span status to ERROR"""
        self._ensure_setup('test_500_sets_error_span_status', ['pip install opentelemetry-sdk fastapi httpx pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_observability.py', '-v', '-k', 'test_error_span'], timeout=120)
        assert result.returncode == 0, (
            f'test_500_sets_error_span_status failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_exporter_failure_non_fatal(self):
        """Verify unreachable OTLP endpoint does not crash application"""
        self._ensure_setup('test_exporter_failure_non_fatal', ['pip install opentelemetry-sdk opentelemetry-exporter-otlp fastapi httpx'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import os; os.environ['OTEL_EXPORTER_OTLP_ENDPOINT']='http://localhost:99999'; from docs.examples.observability_demo.app import app; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_exporter_failure_non_fatal failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_invalid_log_level_defaults_to_info(self):
        """Verify invalid OTEL_LOG_LEVEL env var defaults to INFO"""
        self._ensure_setup('test_invalid_log_level_defaults_to_info', ['pip install opentelemetry-sdk structlog'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import os; os.environ['OTEL_LOG_LEVEL']='INVALID_LEVEL'; from docs.examples.observability_demo.logging_config import configure_logging; configure_logging(); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_invalid_log_level_defaults_to_info failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_full_observability_suite(self):
        """Run the complete observability test suite"""
        self._ensure_setup('test_full_observability_suite', ['pip install opentelemetry-sdk opentelemetry-api structlog fastapi pytest httpx'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_observability.py', '-v', '--tb=short'], timeout=120)
        assert result.returncode == 0, (
            f'test_full_observability_suite failed (exit {result.returncode})\n' + result.stderr[:500]
        )

