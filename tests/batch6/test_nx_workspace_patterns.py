"""
Tests for 'nx-workspace-patterns' skill.
Generated from benchmark case definitions for nx-workspace-patterns.
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


class TestNxWorkspacePatterns:
    """Verify the nx-workspace-patterns skill output."""

    REPO_DIR = '/workspace/nx'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestNxWorkspacePatterns.REPO_DIR, rel)

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

    def test_nx_json_exists(self):
        """Verify nx.json exists at workspace root"""
        _p = self._repo_path('nx.json')
        assert os.path.isfile(_p), f'Missing file: nx.json'
        self._load_json(_p)  # parse check

    def test_project_json_files_exist(self):
        """Verify at least 3 project.json files exist"""
        _p = self._repo_path('apps/')
        assert os.path.isdir(_p), f'Missing directory: apps/'
        _files = glob.glob(os.path.join(_p, '*.yaml')) + glob.glob(os.path.join(_p, '*.yml')) + glob.glob(os.path.join(_p, '*.json')) + glob.glob(os.path.join(_p, '*.py')) + glob.glob(os.path.join(_p, '*.java')) + glob.glob(os.path.join(_p, '*.js')) + glob.glob(os.path.join(_p, '*.go'))
        assert len(_files) >= 3, f'Expected >= 3 files, found {len(_files)}'
        _p = self._repo_path('libs/')
        assert os.path.isdir(_p), f'Missing directory: libs/'
        _files = glob.glob(os.path.join(_p, '*.yaml')) + glob.glob(os.path.join(_p, '*.yml')) + glob.glob(os.path.join(_p, '*.json')) + glob.glob(os.path.join(_p, '*.py')) + glob.glob(os.path.join(_p, '*.java')) + glob.glob(os.path.join(_p, '*.js')) + glob.glob(os.path.join(_p, '*.go'))
        assert len(_files) >= 3, f'Expected >= 3 files, found {len(_files)}'

    # ── semantic_check (static) ────────────────────────────────────────

    def test_nx_json_has_target_defaults(self):
        """Verify nx.json has targetDefaults key"""
        _p = self._repo_path('nx.json')
        assert os.path.exists(_p), f'Missing: nx.json'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'targetDefaults' in _all, 'Missing: targetDefaults'

    def test_named_inputs_production(self):
        """Verify namedInputs.production excludes test files"""
        _p = self._repo_path('nx.json')
        assert os.path.exists(_p), f'Missing: nx.json'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'namedInputs' in _all, 'Missing: namedInputs'
        assert 'production' in _all, 'Missing: production'
        assert '!' in _all, 'Missing: !'

    def test_project_has_targets_and_tags(self):
        """Verify project.json files have targets and tags"""
        _p = self._repo_path('**/project.json')
        assert os.path.exists(_p), f'Missing: **/project.json'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'targets' in _all, 'Missing: targets'
        assert 'tags' in _all, 'Missing: tags'

    def test_build_cache_enabled(self):
        """Verify targetDefaults.build has cache: true"""
        _p = self._repo_path('nx.json')
        assert os.path.exists(_p), f'Missing: nx.json'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'cache' in _all, 'Missing: cache'
        assert 'true' in _all, 'Missing: true'

    # ── functional_check ────────────────────────────────────────

    def test_nx_json_valid_json(self):
        """Verify nx.json is valid JSON with required keys"""
        result = self._run_cmd('python', args=['-c', "import json; nx=json.loads(open('nx.json').read()); assert 'targetDefaults' in nx; assert 'namedInputs' in nx; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_nx_json_valid_json failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_production_excludes_spec_files(self):
        """Verify production namedInput excludes spec/test files"""
        result = self._run_cmd('python', args=['-c', "import json; nx=json.loads(open('nx.json').read()); prod=nx['namedInputs']['production']; negations=[i for i in prod if isinstance(i,str) and '!' in i]; assert len(negations)>0, f'No negation patterns in production: {prod}'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_production_excludes_spec_files failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_project_count_minimum(self):
        """Verify at least 3 project.json files exist"""
        result = self._run_cmd('python', args=['-c', "import glob; files=glob.glob('**/project.json',recursive=True); files=[f for f in files if 'node_modules' not in f]; assert len(files)>=3, f'Only {len(files)} projects'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_project_count_minimum failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_project_targets_build_test(self):
        """Verify each project has build and test targets"""
        result = self._run_cmd('python', args=['-c', "import json,glob; files=[f for f in glob.glob('**/project.json',recursive=True) if 'node_modules' not in f]\nfor f in files:\n    p=json.loads(open(f).read())\n    targets=p.get('targets',{})\n    assert 'build' in targets or 'test' in targets, f'{f}: missing build/test targets'\nprint('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_project_targets_build_test failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_tags_nonempty(self):
        """Verify each project has non-empty tags array"""
        result = self._run_cmd('python', args=['-c', "import json,glob; files=[f for f in glob.glob('**/project.json',recursive=True) if 'node_modules' not in f]\nfor f in files:\n    p=json.loads(open(f).read())\n    tags=p.get('tags',[])\n    assert len(tags)>0, f'{f}: empty tags'\nprint('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_tags_nonempty failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_build_cache_true(self):
        """Verify targetDefaults.build.cache is true"""
        result = self._run_cmd('python', args=['-c', "import json; nx=json.loads(open('nx.json').read()); cache=nx.get('targetDefaults',{}).get('build',{}).get('cache'); assert cache==True, f'Build cache is {cache}'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_build_cache_true failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

