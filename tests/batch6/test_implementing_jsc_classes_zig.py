"""
Tests for 'implementing-jsc-classes-zig' skill.
Generated from benchmark case definitions for implementing-jsc-classes-zig.
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


class TestImplementingJscClassesZig:
    """Verify the implementing-jsc-classes-zig skill output."""

    REPO_DIR = '/workspace/bun'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestImplementingJscClassesZig.REPO_DIR, rel)

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

    def test_cron_classes_ts_exists(self):
        """Verify cron.classes.ts TypeScript definition exists"""
        _p = self._repo_path('src/bun.js/api/bun/cron.classes.ts')
        assert os.path.isfile(_p), f'Missing file: src/bun.js/api/bun/cron.classes.ts'

    def test_cron_zig_exists(self):
        """Verify cron.zig Zig implementation exists"""
        _p = self._repo_path('src/bun.js/api/bun/cron.zig')
        assert os.path.isfile(_p), f'Missing file: src/bun.js/api/bun/cron.zig'

    # ── semantic_check (static) ────────────────────────────────────────

    def test_classes_ts_exports_class(self):
        """Verify cron.classes.ts exports BunCronJob or generateClass"""
        _p = self._repo_path('src/bun.js/api/bun/cron.classes.ts')
        assert os.path.exists(_p), f'Missing: src/bun.js/api/bun/cron.classes.ts'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'BunCronJob' in _all, 'Missing: BunCronJob'
        assert 'generateClass' in _all, 'Missing: generateClass'
        assert 'klass' in _all, 'Missing: klass'

    def test_classes_ts_has_methods(self):
        """Verify class definition includes start, stop, isRunning methods"""
        _p = self._repo_path('src/bun.js/api/bun/cron.classes.ts')
        assert os.path.exists(_p), f'Missing: src/bun.js/api/bun/cron.classes.ts'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'start' in _all, 'Missing: start'
        assert 'stop' in _all, 'Missing: stop'
        assert 'isRunning' in _all, 'Missing: isRunning'

    def test_zig_has_zigcronjob_struct(self):
        """Verify cron.zig defines pub const ZigCronJob struct"""
        _p = self._repo_path('src/bun.js/api/bun/cron.zig')
        assert os.path.exists(_p), f'Missing: src/bun.js/api/bun/cron.zig'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'pub const ZigCronJob' in _all, 'Missing: pub const ZigCronJob'

    def test_zig_has_create_finalize(self):
        """Verify cron.zig has create and finalize functions for JSC lifecycle"""
        _p = self._repo_path('src/bun.js/api/bun/cron.zig')
        assert os.path.exists(_p), f'Missing: src/bun.js/api/bun/cron.zig'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'create' in _all, 'Missing: create'
        assert 'finalize' in _all, 'Missing: finalize'

    # ── functional_check ────────────────────────────────────────

    def test_zig_struct_grep_definition(self):
        """Verify ZigCronJob struct is defined via grep"""
        result = self._run_cmd('grep', args=['-n', 'ZigCronJob', 'src/bun.js/api/bun/cron.zig'], timeout=120)
        assert result.returncode == 0, (
            f'test_zig_struct_grep_definition failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_classes_ts_class_export_grep(self):
        """Verify BunCronJob or generateClass exported via grep"""
        result = self._run_cmd('grep', args=['-nE', 'BunCronJob|generateClass|klass', 'src/bun.js/api/bun/cron.classes.ts'], timeout=120)
        assert result.returncode == 0, (
            f'test_classes_ts_class_export_grep failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_method_names_match_ts_zig(self):
        """Verify method names in .classes.ts appear in .zig for consistent binding"""
        result = self._run_cmd('python', args=['-c', "import re\nts=open('src/bun.js/api/bun/cron.classes.ts').read()\nzig=open('src/bun.js/api/bun/cron.zig').read()\nmethods=['start','stop','isRunning']\nfor m in methods:\n    assert m in ts, f'{m} not in .classes.ts'\n    assert m in zig, f'{m} not in .zig'\nprint('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_method_names_match_ts_zig failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_zig_jsc_types_used(self):
        """Verify Zig uses JSC types (JSValue, JSGlobalObject)"""
        result = self._run_cmd('grep', args=['-c', 'JSValue\\|JSGlobalObject', 'src/bun.js/api/bun/cron.zig'], timeout=120)
        assert result.returncode == 0, (
            f'test_zig_jsc_types_used failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_zig_extern_fn_present(self):
        """Verify extern fn callbacks exist for JSC ABI"""
        result = self._run_cmd('grep', args=['-c', 'extern fn\\|export fn', 'src/bun.js/api/bun/cron.zig'], timeout=120)
        assert result.returncode == 0, (
            f'test_zig_extern_fn_present failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_zig_finalize_prevents_leak(self):
        """Verify finalize function exists to prevent memory leaks"""
        result = self._run_cmd('grep', args=['-n', 'finalize', 'src/bun.js/api/bun/cron.zig'], timeout=120)
        assert result.returncode == 0, (
            f'test_zig_finalize_prevents_leak failed (exit {result.returncode})\n' + result.stderr[:500]
        )

