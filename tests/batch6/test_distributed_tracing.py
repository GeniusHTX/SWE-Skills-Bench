"""
Tests for 'distributed-tracing' skill.
Generated from benchmark case definitions for distributed-tracing.
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


class TestDistributedTracing:
    """Verify the distributed-tracing skill output."""

    REPO_DIR = '/workspace/opentelemetry-collector'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestDistributedTracing.REPO_DIR, rel)

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

    def test_tracing_init_exists(self):
        """Verify tracing module init file exists"""
        _p = self._repo_path('lib/tracing/__init__.py')
        assert os.path.isfile(_p), f'Missing file: lib/tracing/__init__.py'
        py_compile.compile(_p, doraise=True)

    def test_middleware_file_exists(self):
        """Verify tracing middleware file exists"""
        _p = self._repo_path('lib/tracing/middleware.py')
        assert os.path.isfile(_p), f'Missing file: lib/tracing/middleware.py'
        py_compile.compile(_p, doraise=True)

    def test_test_tracing_exists(self):
        """Verify test file for tracing exists"""
        _p = self._repo_path('tests/test_tracing.py')
        assert os.path.isfile(_p), f'Missing file: tests/test_tracing.py'
        py_compile.compile(_p, doraise=True)

    # ── semantic_check (static) ────────────────────────────────────────

    def test_configure_tracing_function(self):
        """Verify configure_tracing function with service_name parameter"""
        _p = self._repo_path('lib/tracing/__init__.py')
        assert os.path.exists(_p), f'Missing: lib/tracing/__init__.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'def configure_tracing' in _all, 'Missing: def configure_tracing'
        assert 'service_name' in _all, 'Missing: service_name'

    def test_tracing_middleware_class(self):
        """Verify TracingMiddleware class with __call__ method"""
        _p = self._repo_path('lib/tracing/middleware.py')
        assert os.path.exists(_p), f'Missing: lib/tracing/middleware.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'class TracingMiddleware' in _all, 'Missing: class TracingMiddleware'
        assert '__call__' in _all, 'Missing: __call__'

    def test_span_kind_server(self):
        """Verify SpanKind.SERVER used for incoming request spans"""
        _p = self._repo_path('lib/tracing/middleware.py')
        assert os.path.exists(_p), f'Missing: lib/tracing/middleware.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'SpanKind.SERVER' in _all, 'Missing: SpanKind.SERVER'
        assert 'SpanKind' in _all, 'Missing: SpanKind'

    def test_span_end_in_finally(self):
        """Verify span.end() is called in finally block"""
        _p = self._repo_path('lib/tracing/middleware.py')
        assert os.path.exists(_p), f'Missing: lib/tracing/middleware.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'finally' in _all, 'Missing: finally'
        assert re.search('span.end()', _all, re.MULTILINE), 'Pattern not found: span.end()'

    # ── functional_check ────────────────────────────────────────

    def test_configure_tracing_returns_provider(self):
        """Verify configure_tracing returns a non-None TracerProvider"""
        self._ensure_setup('test_configure_tracing_returns_provider', ['pip install opentelemetry-sdk opentelemetry-api'], 'skip_if_setup_fails')
        result = self._run_cmd('python', args=['-c', "from lib.tracing import configure_tracing; tp=configure_tracing('test-svc'); assert tp is not None; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_configure_tracing_returns_provider failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_inmemory_exporter_captures_spans(self):
        """Verify InMemorySpanExporter captures spans after tracer usage"""
        self._ensure_setup('test_inmemory_exporter_captures_spans', ['pip install opentelemetry-sdk'], 'skip_if_setup_fails')
        result = self._run_cmd('python', args=['-c', "from opentelemetry.sdk.trace import TracerProvider; from opentelemetry.sdk.trace.export.in_memory import InMemorySpanExporter; from opentelemetry.sdk.trace.export import SimpleSpanProcessor; exp=InMemorySpanExporter(); tp=TracerProvider(); tp.add_span_processor(SimpleSpanProcessor(exp)); t=tp.get_tracer('test'); s=t.start_span('test-span'); s.end(); assert len(exp.get_finished_spans())>0; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_inmemory_exporter_captures_spans failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_span_attributes_set(self):
        """Verify span has http.method attribute set"""
        self._ensure_setup('test_span_attributes_set', ['pip install opentelemetry-sdk'], 'skip_if_setup_fails')
        result = self._run_cmd('python', args=['-c', "from opentelemetry.sdk.trace import TracerProvider; from opentelemetry.sdk.trace.export.in_memory import InMemorySpanExporter; from opentelemetry.sdk.trace.export import SimpleSpanProcessor; exp=InMemorySpanExporter(); tp=TracerProvider(); tp.add_span_processor(SimpleSpanProcessor(exp)); t=tp.get_tracer('test'); s=t.start_span('request'); s.set_attribute('http.method','GET'); s.end(); span=exp.get_finished_spans()[0]; assert span.attributes.get('http.method')=='GET'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_span_attributes_set failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_exception_sets_error_status(self):
        """Verify exception in span scope sets ERROR status"""
        self._ensure_setup('test_exception_sets_error_status', ['pip install opentelemetry-sdk'], 'skip_if_setup_fails')
        result = self._run_cmd('python', args=['-c', "from opentelemetry.sdk.trace import TracerProvider; from opentelemetry.sdk.trace.export.in_memory import InMemorySpanExporter; from opentelemetry.sdk.trace.export import SimpleSpanProcessor; from opentelemetry.trace import StatusCode; exp=InMemorySpanExporter(); tp=TracerProvider(); tp.add_span_processor(SimpleSpanProcessor(exp)); t=tp.get_tracer('test')\ntry:\n    with t.start_as_current_span('err-span') as s:\n        s.set_status(StatusCode.ERROR, 'test error')\n        raise ValueError('boom')\nexcept ValueError:\n    pass\nspan=exp.get_finished_spans()[0]; assert span.status.status_code==StatusCode.ERROR; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_exception_sets_error_status failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_traceparent_propagation(self):
        """Verify W3C traceparent header propagation code exists"""
        _p = self._repo_path('lib/tracing/__init__.py')
        assert os.path.exists(_p), f'Missing: lib/tracing/__init__.py'
        _contents = self._safe_read(_p)
        _p = self._repo_path('lib/tracing/middleware.py')
        assert os.path.exists(_p), f'Missing: lib/tracing/middleware.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'propagate' in _all, 'Missing: propagate'
        assert 'inject' in _all, 'Missing: inject'
        assert 'traceparent' in _all, 'Missing: traceparent'

