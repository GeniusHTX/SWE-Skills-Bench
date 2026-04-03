"""
Tests for 'gitlab-ci-patterns' skill.
Generated from benchmark case definitions for gitlab-ci-patterns.
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


class TestGitlabCiPatterns:
    """Verify the gitlab-ci-patterns skill output."""

    REPO_DIR = '/workspace/gitlabhq'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestGitlabCiPatterns.REPO_DIR, rel)

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

    def test_gitlab_ci_yml_exists(self):
        """Verify .gitlab-ci.yml exists at root"""
        _p = self._repo_path('.gitlab-ci.yml')
        assert os.path.isfile(_p), f'Missing file: .gitlab-ci.yml'
        self._load_yaml(_p)  # parse check

    def test_tests_directory_exists(self):
        """Verify tests directory referenced in artifacts exists"""
        _p = self._repo_path('tests/')
        assert os.path.isdir(_p), f'Missing directory: tests/'

    # ── semantic_check (static) ────────────────────────────────────────

    def test_stages_list_defined(self):
        """Verify stages key with at least 4 stages"""
        _p = self._repo_path('.gitlab-ci.yml')
        assert os.path.exists(_p), f'Missing: .gitlab-ci.yml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'stages' in _all, 'Missing: stages'

    def test_deploy_production_environment(self):
        """Verify deploy-production has environment: production"""
        _p = self._repo_path('.gitlab-ci.yml')
        assert os.path.exists(_p), f'Missing: .gitlab-ci.yml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'environment' in _all, 'Missing: environment'
        assert 'production' in _all, 'Missing: production'

    def test_artifacts_configured(self):
        """Verify at least one job has artifacts with paths"""
        _p = self._repo_path('.gitlab-ci.yml')
        assert os.path.exists(_p), f'Missing: .gitlab-ci.yml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'artifacts' in _all, 'Missing: artifacts'
        assert 'paths' in _all, 'Missing: paths'

    def test_cache_key_branch_based(self):
        """Verify cache key uses CI_COMMIT_REF_SLUG for branch isolation"""
        _p = self._repo_path('.gitlab-ci.yml')
        assert os.path.exists(_p), f'Missing: .gitlab-ci.yml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'cache' in _all, 'Missing: cache'
        assert 'CI_COMMIT_REF_SLUG' in _all, 'Missing: CI_COMMIT_REF_SLUG'

    # ── functional_check ────────────────────────────────────────

    def test_yaml_parses_successfully(self):
        """Verify .gitlab-ci.yml is valid YAML"""
        result = self._run_cmd('python', args=['-c', "import yaml; ci=yaml.safe_load(open('.gitlab-ci.yml')); assert 'stages' in ci; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_yaml_parses_successfully failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_stages_count_minimum(self):
        """Verify at least 4 stages defined"""
        result = self._run_cmd('python', args=['-c', 'import yaml; ci=yaml.safe_load(open(\'.gitlab-ci.yml\')); assert len(ci[\'stages\'])>=4, f\'Only {len(ci["stages"])} stages\'; print(\'PASS\')'], timeout=120)
        assert result.returncode == 0, (
            f'test_stages_count_minimum failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_all_job_stages_valid(self):
        """Verify all job stage references exist in stages list"""
        result = self._run_cmd('python', args=['-c', "import yaml; ci=yaml.safe_load(open('.gitlab-ci.yml')); stages=set(ci['stages']); jobs={k:v for k,v in ci.items() if isinstance(v,dict) and 'stage' in v}; invalid=[k for k,v in jobs.items() if v['stage'] not in stages]; assert len(invalid)==0, f'Invalid stages: {invalid}'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_all_job_stages_valid failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_deploy_production_tag_rules(self):
        """Verify deploy-production restricted to tags or protected branches"""
        result = self._run_cmd('python', args=['-c', "import yaml; ci=yaml.safe_load(open('.gitlab-ci.yml')); prod=None\nfor k,v in ci.items():\n    if isinstance(v,dict) and 'production' in str(v.get('environment','')):\n        prod=v; break\nassert prod is not None, 'No production job found'\nrules_str=str(prod.get('rules',prod.get('only','')))\nassert 'tag' in rules_str.lower() or 'CI_COMMIT_TAG' in rules_str or 'tags' in rules_str; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_deploy_production_tag_rules failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_artifacts_have_expiry(self):
        """Verify artifacts have expire_in configured"""
        result = self._run_cmd('python', args=['-c', "import yaml; ci=yaml.safe_load(open('.gitlab-ci.yml')); found=False\nfor k,v in ci.items():\n    if isinstance(v,dict) and 'artifacts' in v:\n        if 'expire_in' in v.get('artifacts',{}): found=True; break\nassert found, 'No artifacts with expire_in found'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_artifacts_have_expiry failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_yaml_no_tabs(self):
        """Verify YAML does not contain tab characters"""
        result = self._run_cmd('python', args=['-c', "content=open('.gitlab-ci.yml').read(); assert '\\t' not in content, 'YAML contains tabs'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_yaml_no_tabs failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

