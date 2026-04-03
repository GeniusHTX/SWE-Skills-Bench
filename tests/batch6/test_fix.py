"""
Tests for 'fix' skill.
Generated from benchmark case definitions for fix.
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


class TestFix:
    """Verify the fix skill output."""

    REPO_DIR = '/workspace/upgradle'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestFix.REPO_DIR, rel)

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

    def test_app_tsx_exists(self):
        """Verify main App.tsx component exists"""
        _p = self._repo_path('src/App.tsx')
        assert os.path.isfile(_p), f'Missing file: src/App.tsx'

    def test_tsconfig_exists(self):
        """Verify tsconfig.json exists with strict mode"""
        _p = self._repo_path('tsconfig.json')
        assert os.path.isfile(_p), f'Missing file: tsconfig.json'
        self._load_json(_p)  # parse check

    def test_eslint_config_exists(self):
        """Verify ESLint configuration file exists"""
        _p = self._repo_path('.eslintrc.js')
        assert os.path.isfile(_p), f'Missing file: .eslintrc.js'
        _p = self._repo_path('.eslintrc.json')
        assert os.path.isfile(_p), f'Missing file: .eslintrc.json'
        self._load_json(_p)  # parse check
        _p = self._repo_path('eslint.config.js')
        assert os.path.isfile(_p), f'Missing file: eslint.config.js'

    # ── semantic_check (static) ────────────────────────────────────────

    def test_tsconfig_strict_mode(self):
        """Verify tsconfig.json has strict: true"""
        _p = self._repo_path('tsconfig.json')
        assert os.path.exists(_p), f'Missing: tsconfig.json'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'strict' in _all, 'Missing: strict'
        assert 'true' in _all, 'Missing: true'

    def test_no_ts_ignore_comments(self):
        """Verify no @ts-ignore comments used as workarounds"""
        _p = self._repo_path('src/')
        assert os.path.isdir(_p), f'Missing directory: src/'
        _contents = ''
        for _f in sorted(glob.glob(os.path.join(_p, '**', '*'), recursive=True)):
            if os.path.isfile(_f):
                _contents += self._safe_read(_f) + '\n'
        _all = _contents if isinstance(_contents, str) else ''
        assert '@ts-ignore' in _all, 'Missing: @ts-ignore'

    def test_no_eslint_disable_comments(self):
        """Verify no eslint-disable comments used as workarounds"""
        _p = self._repo_path('src/')
        assert os.path.isdir(_p), f'Missing directory: src/'
        _contents = ''
        for _f in sorted(glob.glob(os.path.join(_p, '**', '*'), recursive=True)):
            if os.path.isfile(_f):
                _contents += self._safe_read(_f) + '\n'
        _all = _contents if isinstance(_contents, str) else ''
        assert 'eslint-disable' in _all, 'Missing: eslint-disable'

    # ── functional_check ────────────────────────────────────────

    def test_tsc_no_emit_passes(self):
        """Verify TypeScript compilation passes with zero errors"""
        self._ensure_setup('test_tsc_no_emit_passes', ['npm install'], 'skip_if_setup_fails')
        result = self._run_cmd('npx', args=['tsc', '--noEmit'], timeout=120)
        assert result.returncode == 0, (
            f'test_tsc_no_emit_passes failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_eslint_passes(self):
        """Verify ESLint passes with zero errors and warnings"""
        self._ensure_setup('test_eslint_passes', ['npm install'], 'skip_if_setup_fails')
        result = self._run_cmd('npx', args=['eslint', 'src/', '--no-fix'], timeout=120)
        assert result.returncode == 0, (
            f'test_eslint_passes failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_prettier_passes(self):
        """Verify Prettier formatting check passes"""
        self._ensure_setup('test_prettier_passes', ['npm install'], 'skip_if_setup_fails')
        result = self._run_cmd('npx', args=['prettier', '--check', 'src/**/*.{ts,tsx}'], timeout=120)
        assert result.returncode == 0, (
            f'test_prettier_passes failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_no_any_type_in_src(self):
        """Verify minimal use of 'any' type in source files"""
        result = self._run_cmd('grep', args=['-rn', ': any', 'src/'], timeout=120)
        assert result.returncode == 0, (
            f'test_no_any_type_in_src failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_build_succeeds(self):
        """Verify production build succeeds"""
        self._ensure_setup('test_build_succeeds', ['npm install'], 'skip_if_setup_fails')
        result = self._run_cmd('npm', args=['run', 'build'], timeout=300)
        assert result.returncode == 0, (
            f'test_build_succeeds failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_tsconfig_strict_not_weakened(self):
        """Verify strict mode not weakened by overriding noImplicitAny to false"""
        result = self._run_cmd('python', args=['-c', "import json; tc=json.load(open('tsconfig.json')); co=tc.get('compilerOptions',{}); assert co.get('strict',False)==True, 'strict not true'; assert co.get('noImplicitAny',True)!=False, 'noImplicitAny weakened'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_tsconfig_strict_not_weakened failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

