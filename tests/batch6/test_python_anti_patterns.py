"""
Tests for 'python-anti-patterns' skill.
Generated from benchmark case definitions for python-anti-patterns.
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


class TestPythonAntiPatterns:
    """Verify the python-anti-patterns skill output."""

    REPO_DIR = '/workspace/boltons'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestPythonAntiPatterns.REPO_DIR, rel)

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

    def test_iterutils_exists(self):
        """Verify refactored iterutils.py exists"""
        _p = self._repo_path('boltons/iterutils.py')
        assert os.path.isfile(_p), f'Missing file: boltons/iterutils.py'
        py_compile.compile(_p, doraise=True)

    def test_fileutils_exists(self):
        """Verify refactored fileutils.py exists"""
        _p = self._repo_path('boltons/fileutils.py')
        assert os.path.isfile(_p), f'Missing file: boltons/fileutils.py'
        py_compile.compile(_p, doraise=True)

    # ── semantic_check (static) ────────────────────────────────────────

    def test_no_mutable_defaults(self):
        """Verify no mutable default arguments remain in function signatures"""
        _p = self._repo_path('boltons/iterutils.py')
        assert os.path.exists(_p), f'Missing: boltons/iterutils.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert re.search('=[]', _all, re.MULTILINE), 'Pattern not found: =[]'
        assert '={}' in _all, 'Missing: ={}'

    def test_no_bare_except(self):
        """Verify no bare except: clauses remain"""
        _p = self._repo_path('boltons/iterutils.py')
        assert os.path.exists(_p), f'Missing: boltons/iterutils.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'except:' in _all, 'Missing: except:'

    def test_isinstance_usage(self):
        """Verify isinstance used instead of type() comparisons"""
        _p = self._repo_path('boltons/iterutils.py')
        assert os.path.exists(_p), f'Missing: boltons/iterutils.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'isinstance' in _all, 'Missing: isinstance'
        assert re.search('type(', _all, re.MULTILINE), 'Pattern not found: type('

    # ── functional_check ────────────────────────────────────────

    def test_chunked_preserves_behavior(self):
        """Verify chunked still works correctly for normal inputs"""
        self._ensure_setup('test_chunked_preserves_behavior', ['pip install boltons'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from boltons.iterutils import chunked; assert list(chunked([1,2,3,4,5],2))==[[1,2],[3,4],[5]]; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_chunked_preserves_behavior failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_chunked_zero_raises(self):
        """Verify chunked(src, 0) raises ValueError"""
        self._ensure_setup('test_chunked_zero_raises', ['pip install boltons'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from boltons.iterutils import chunked\ntry:\n    chunked([1,2,3], 0)\n    assert False, 'Should have raised'\nexcept ValueError as e:\n    assert 'positive' in str(e).lower(); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_chunked_zero_raises failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_chunked_negative_raises(self):
        """Verify chunked(src, -1) raises ValueError"""
        self._ensure_setup('test_chunked_negative_raises', ['pip install boltons'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from boltons.iterutils import chunked\ntry:\n    chunked([1,2,3], -1)\n    assert False, 'Should have raised'\nexcept ValueError as e:\n    assert 'positive' in str(e).lower(); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_chunked_negative_raises failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_bucketize_no_shared_state(self):
        """Verify bucketize called twice has no shared mutable state"""
        self._ensure_setup('test_bucketize_no_shared_state', ['pip install boltons'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from boltons.iterutils import bucketize; r1=bucketize(range(5), key=lambda x: x%2); r2=bucketize(range(3), key=lambda x: x%2); assert r1!=r2 or len(r1[0])!=len(r2[0]); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_bucketize_no_shared_state failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_first_empty_returns_none(self):
        """Verify first([]) returns None without error"""
        self._ensure_setup('test_first_empty_returns_none', ['pip install boltons'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from boltons.iterutils import first; assert first([])==None; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_first_empty_returns_none failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_atomic_save_type_error(self):
        """Verify atomic_save(123) raises TypeError"""
        self._ensure_setup('test_atomic_save_type_error', ['pip install boltons'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from boltons.fileutils import atomic_save\ntry:\n    atomic_save(123)\n    assert False, 'Should have raised'\nexcept TypeError:\n    print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_atomic_save_type_error failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_pytest_refactor_suite(self):
        """Run the full refactor test suite"""
        self._ensure_setup('test_pytest_refactor_suite', ['pip install boltons pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/', '-v', '--tb=short'], timeout=120)
        assert result.returncode == 0, (
            f'test_pytest_refactor_suite failed (exit {result.returncode})\n' + result.stderr[:500]
        )

