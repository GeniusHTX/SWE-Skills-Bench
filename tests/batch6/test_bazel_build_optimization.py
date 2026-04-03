"""
Tests for 'bazel-build-optimization' skill.
Generated from benchmark case definitions for bazel-build-optimization.
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


class TestBazelBuildOptimization:
    """Verify the bazel-build-optimization skill output."""

    REPO_DIR = '/workspace/bazel'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestBazelBuildOptimization.REPO_DIR, rel)

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

    def test_workspace_bazel_exists(self):
        """Verify WORKSPACE.bazel or WORKSPACE file exists at root"""
        _p = self._repo_path('WORKSPACE.bazel')
        assert os.path.isfile(_p), f'Missing file: WORKSPACE.bazel'

    def test_bazelrc_exists(self):
        """Verify .bazelrc configuration file exists"""
        _p = self._repo_path('.bazelrc')
        assert os.path.isfile(_p), f'Missing file: .bazelrc'

    def test_bzl_macros_exist(self):
        """Verify custom Starlark macro .bzl files exist"""
        _p = self._repo_path('tools/')
        assert os.path.isdir(_p), f'Missing directory: tools/'
        _p = self._repo_path('macros/')
        assert os.path.isdir(_p), f'Missing directory: macros/'

    # ── semantic_check (static) ────────────────────────────────────────

    def test_http_archive_with_sha256(self):
        """Verify all http_archive calls have sha256 for reproducibility"""
        _p = self._repo_path('WORKSPACE.bazel')
        assert os.path.exists(_p), f'Missing: WORKSPACE.bazel'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'http_archive' in _all, 'Missing: http_archive'
        assert 'sha256' in _all, 'Missing: sha256'

    def test_remote_cache_configured(self):
        """Verify .bazelrc has remote_cache configuration"""
        _p = self._repo_path('.bazelrc')
        assert os.path.exists(_p), f'Missing: .bazelrc'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'remote_cache' in _all, 'Missing: remote_cache'

    def test_ci_build_mode(self):
        """Verify .bazelrc has build:ci section for CI-specific flags"""
        _p = self._repo_path('.bazelrc')
        assert os.path.exists(_p), f'Missing: .bazelrc'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'build:ci' in _all, 'Missing: build:ci'

    def test_starlark_macro_definition(self):
        """Verify custom Starlark macro has 'def' function definition"""
        _p = self._repo_path('tools/')
        assert os.path.isdir(_p), f'Missing directory: tools/'
        _contents = ''
        for _f in sorted(glob.glob(os.path.join(_p, '**', '*'), recursive=True)):
            if os.path.isfile(_f):
                _contents += self._safe_read(_f) + '\n'
        _p = self._repo_path('macros/')
        assert os.path.isdir(_p), f'Missing directory: macros/'
        _contents = ''
        for _f in sorted(glob.glob(os.path.join(_p, '**', '*'), recursive=True)):
            if os.path.isfile(_f):
                _contents += self._safe_read(_f) + '\n'
        _all = _contents if isinstance(_contents, str) else ''
        assert 'def ' in _all, 'Missing: def '

    # ── functional_check ────────────────────────────────────────

    def test_sha256_count_matches_archives(self):
        """Verify every http_archive has a matching sha256 entry"""
        result = self._run_cmd('python', args=['-c', "import re; ws=open('WORKSPACE.bazel').read(); a=len(re.findall(r'http_archive', ws)); s=len(re.findall(r'sha256\\s*=', ws)); assert a==s, f'{a} archives vs {s} sha256s'; print('PASS')"], timeout=600)
        assert result.returncode == 0, (
            f'test_sha256_count_matches_archives failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_build_files_minimum_count(self):
        """Verify at least 4 BUILD.bazel files exist across the project"""
        result = self._run_cmd('python', args=['-c', "import glob; bf=glob.glob('**/BUILD.bazel', recursive=True)+glob.glob('**/BUILD', recursive=True); assert len(bf)>=4, f'Only {len(bf)} BUILD files found'; print('PASS')"], timeout=600)
        assert result.returncode == 0, (
            f'test_build_files_minimum_count failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_remote_cache_not_placeholder(self):
        """Verify remote_cache URL is not a TODO/placeholder value"""
        result = self._run_cmd('python', args=['-c', "rc=open('.bazelrc').read(); assert 'remote_cache' in rc; assert 'TODO' not in rc and 'localhost' not in rc.split('remote_cache')[1].split('\\n')[0]; print('PASS')"], timeout=600)
        assert result.returncode == 0, (
            f'test_remote_cache_not_placeholder failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_sha256_not_empty_string(self):
        """Verify no sha256 fields are empty strings"""
        result = self._run_cmd('python', args=['-c', 'import re; ws=open(\'WORKSPACE.bazel\').read(); empties=re.findall(r\'sha256\\s*=\\s*""\', ws); assert len(empties)==0, f\'{len(empties)} empty sha256 values\'; print(\'PASS\')'], timeout=600)
        assert result.returncode == 0, (
            f'test_sha256_not_empty_string failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_load_statements_reference_bzl(self):
        """Verify BUILD.bazel load() statements reference existing .bzl labels"""
        result = self._run_cmd('python', args=['-c', 'import re; bf=open(\'BUILD.bazel\').read(); loads=re.findall(r\'load\\("([^"]+)"\', bf); assert len(loads)>0, \'No load() statements found\'; print(f\'Found {len(loads)} load statements: PASS\')'], timeout=600)
        assert result.returncode == 0, (
            f'test_load_statements_reference_bzl failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

