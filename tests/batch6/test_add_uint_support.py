"""
Tests for 'add-uint-support' skill.
Generated from benchmark case definitions for add-uint-support.
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


class TestAddUintSupport:
    """Verify the add-uint-support skill output."""

    REPO_DIR = '/workspace/pytorch'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestAddUintSupport.REPO_DIR, rel)

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

    def test_uint_ops_file_exists(self):
        """Verify the uint ops implementation file exists"""
        _p = self._repo_path('aten/src/ATen/native/uint_ops.cpp')
        assert os.path.isfile(_p), f'Missing file: aten/src/ATen/native/uint_ops.cpp'

    def test_uint_test_file_exists(self):
        """Verify Python test file for uint ops exists"""
        _p = self._repo_path('test/test_uint_ops.py')
        assert os.path.isfile(_p), f'Missing file: test/test_uint_ops.py'
        py_compile.compile(_p, doraise=True)

    def test_native_functions_yaml_modified(self):
        """Verify native_functions.yaml includes uint dispatch entries"""
        _p = self._repo_path('aten/src/ATen/native/native_functions.yaml')
        assert os.path.isfile(_p), f'Missing file: aten/src/ATen/native/native_functions.yaml'
        self._load_yaml(_p)  # parse check

    # ── semantic_check (static) ────────────────────────────────────────

    def test_uint16_dispatch_registered(self):
        """Verify dispatch registration for uint16 in C++ source"""
        _p = self._repo_path('aten/src/ATen/native/uint_ops.cpp')
        assert os.path.exists(_p), f'Missing: aten/src/ATen/native/uint_ops.cpp'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'uint16' in _all, 'Missing: uint16'
        assert 'kUInt16' in _all, 'Missing: kUInt16'
        assert 'ScalarType::UInt16' in _all, 'Missing: ScalarType::UInt16'

    def test_test_file_imports_uint_dtypes(self):
        """Verify test file uses torch.uint16/uint32/uint64 dtypes"""
        _p = self._repo_path('test/test_uint_ops.py')
        assert os.path.exists(_p), f'Missing: test/test_uint_ops.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'torch.uint16' in _all, 'Missing: torch.uint16'
        assert 'torch.uint32' in _all, 'Missing: torch.uint32'
        assert 'torch.uint64' in _all, 'Missing: torch.uint64'

    def test_arithmetic_ops_in_tests(self):
        """Verify test file contains arithmetic operator tests for unsigned types"""
        _p = self._repo_path('test/test_uint_ops.py')
        assert os.path.exists(_p), f'Missing: test/test_uint_ops.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'add' in _all, 'Missing: add'
        assert 'sub' in _all, 'Missing: sub'
        assert 'mul' in _all, 'Missing: mul'

    def test_comparison_ops_structure(self):
        """Verify comparison operator tests exist for unsigned types"""
        _p = self._repo_path('test/test_uint_ops.py')
        assert os.path.exists(_p), f'Missing: test/test_uint_ops.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'eq' in _all, 'Missing: eq'
        assert 'ne' in _all, 'Missing: ne'
        assert 'lt' in _all, 'Missing: lt'
        assert 'gt' in _all, 'Missing: gt'
        assert 'bool' in _all, 'Missing: bool'

    # ── functional_check ────────────────────────────────────────

    def test_uint16_dtype_accessible(self):
        """Verify torch.uint16 attribute exists at Python level"""
        result = self._run_cmd('python', args=['-c', "import torch; assert hasattr(torch, 'uint16'), 'torch.uint16 not found'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_uint16_dtype_accessible failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_uint16_tensor_creation_dtype(self):
        """Verify tensor created with torch.uint16 retains correct dtype"""
        result = self._run_cmd('python', args=['-c', "import torch; t=torch.tensor([0, 65535], dtype=torch.uint16); assert t.dtype == torch.uint16; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_uint16_tensor_creation_dtype failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_uint16_overflow_wraps(self):
        """Verify uint16 overflow wraps around (65535+1=0)"""
        result = self._run_cmd('python', args=['-c', "import torch; r=(torch.tensor([65535], dtype=torch.uint16)+1).item(); assert r==0, f'Expected 0 got {r}'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_uint16_overflow_wraps failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_uint8_backward_compatibility(self):
        """Verify existing uint8 operations still work (regression check)"""
        result = self._run_cmd('python', args=['-c', "import torch; t=torch.tensor([255], dtype=torch.uint8); assert t.dtype==torch.uint8; assert (t+1).item()==0; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_uint8_backward_compatibility failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_comparison_returns_bool_dtype(self):
        """Verify comparison of uint16 tensors returns bool dtype"""
        result = self._run_cmd('python', args=['-c', "import torch; a=torch.tensor([1],dtype=torch.uint16); b=torch.tensor([2],dtype=torch.uint16); assert (a<b).dtype==torch.bool; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_comparison_returns_bool_dtype failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

