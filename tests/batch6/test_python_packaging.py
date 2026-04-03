"""
Tests for 'python-packaging' skill.
Generated from benchmark case definitions for python-packaging.
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


class TestPythonPackaging:
    """Verify the python-packaging skill output."""

    REPO_DIR = '/workspace/packaging'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestPythonPackaging.REPO_DIR, rel)

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

    def test_cli_module_exists(self):
        """Verify CLI module exists"""
        _p = self._repo_path('src/version_inspector/cli.py')
        assert os.path.isfile(_p), f'Missing file: src/version_inspector/cli.py'
        py_compile.compile(_p, doraise=True)

    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml with entry point exists"""
        _p = self._repo_path('pyproject.toml')
        assert os.path.isfile(_p), f'Missing file: pyproject.toml'

    # ── semantic_check (static) ────────────────────────────────────────

    def test_click_group_decorator(self):
        """Verify @click.group() on main CLI function"""
        _p = self._repo_path('src/version_inspector/cli.py')
        assert os.path.exists(_p), f'Missing: src/version_inspector/cli.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert '@click.group' in _all, 'Missing: @click.group'
        assert 'click.group' in _all, 'Missing: click.group'

    def test_subcommands_defined(self):
        """Verify all 4 subcommands registered"""
        _p = self._repo_path('src/version_inspector/cli.py')
        assert os.path.exists(_p), f'Missing: src/version_inspector/cli.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'parse' in _all, 'Missing: parse'
        assert 'validate' in _all, 'Missing: validate'
        assert 'compare' in _all, 'Missing: compare'
        assert 'bump' in _all, 'Missing: bump'

    def test_entry_point_in_pyproject(self):
        """Verify version-inspector entry point registered"""
        _p = self._repo_path('pyproject.toml')
        assert os.path.exists(_p), f'Missing: pyproject.toml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'version-inspector' in _all, 'Missing: version-inspector'
        assert 'project.scripts' in _all, 'Missing: project.scripts'

    def test_semver_regex_or_library(self):
        """Verify SemVer parsing uses regex or semver library"""
        _p = self._repo_path('src/version_inspector/cli.py')
        assert os.path.exists(_p), f'Missing: src/version_inspector/cli.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 're.compile' in _all, 'Missing: re.compile'
        assert 'semver' in _all, 'Missing: semver'
        assert 'major' in _all, 'Missing: major'
        assert 'minor' in _all, 'Missing: minor'
        assert 'patch' in _all, 'Missing: patch'
        assert 'prerelease' in _all, 'Missing: prerelease'
        assert 'build' in _all, 'Missing: build'

    # ── functional_check ────────────────────────────────────────

    def test_parse_basic_version(self):
        """Verify parse outputs correct JSON for basic version"""
        self._ensure_setup('test_parse_basic_version', ['pip install -e .'], 'fail_if_missing')
        result = self._run_cmd('version-inspector', args=['parse', '1.2.3'], timeout=120)
        assert result.returncode == 0, (
            f'test_parse_basic_version failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_parse_prerelease_and_build(self):
        """Verify parse handles prerelease and build metadata"""
        self._ensure_setup('test_parse_prerelease_and_build', ['pip install -e .'], 'fail_if_missing')
        result = self._run_cmd('version-inspector', args=['parse', '1.2.3-alpha.1+build.42'], timeout=120)
        assert result.returncode == 0, (
            f'test_parse_prerelease_and_build failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_validate_valid_and_invalid(self):
        """Verify validate returns correct exit codes"""
        self._ensure_setup('test_validate_valid_and_invalid', ['pip install -e .'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import subprocess, sys; r1=subprocess.run(['version-inspector','validate','1.2.3']); r2=subprocess.run(['version-inspector','validate','1.2']); assert r1.returncode==0; assert r2.returncode==1; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_validate_valid_and_invalid failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_compare_ordering(self):
        """Verify compare outputs correct ordering"""
        self._ensure_setup('test_compare_ordering', ['pip install -e .'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import subprocess; r=subprocess.run(['version-inspector','compare','2.0.0','1.9.9'],capture_output=True,text=True); assert r.stdout.strip()=='greater'; r2=subprocess.run(['version-inspector','compare','1.0.0','1.0.0'],capture_output=True,text=True); assert r2.stdout.strip()=='equal'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_compare_ordering failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_bump_minor_resets_patch(self):
        """Verify bump minor resets patch to 0"""
        self._ensure_setup('test_bump_minor_resets_patch', ['pip install -e .'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import subprocess; r=subprocess.run(['version-inspector','bump','1.2.3','--part','minor'],capture_output=True,text=True); assert r.stdout.strip()=='1.3.0'; r2=subprocess.run(['version-inspector','bump','1.2.3','--part','major'],capture_output=True,text=True); assert r2.stdout.strip()=='2.0.0'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_bump_minor_resets_patch failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_compare_prerelease_less_than_release(self):
        """Verify prerelease version is less than release per SemVer spec"""
        self._ensure_setup('test_compare_prerelease_less_than_release', ['pip install -e .'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import subprocess; r=subprocess.run(['version-inspector','compare','1.0.0-alpha','1.0.0'],capture_output=True,text=True); assert r.stdout.strip()=='less'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_compare_prerelease_less_than_release failed (exit {result.returncode})\n' + result.stderr[:500]
        )

