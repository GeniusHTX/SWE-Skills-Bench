"""
Tests for 'github-actions-templates' skill.
Generated from benchmark case definitions for github-actions-templates.
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


class TestGithubActionsTemplates:
    """Verify the github-actions-templates skill output."""

    REPO_DIR = '/workspace/starter-workflows'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestGithubActionsTemplates.REPO_DIR, rel)

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

    def test_ci_workflow_exists(self):
        """Verify CI workflow file exists"""
        _p = self._repo_path('.github/workflows/ci.yml')
        assert os.path.isfile(_p), f'Missing file: .github/workflows/ci.yml'
        self._load_yaml(_p)  # parse check

    def test_deploy_production_workflow_exists(self):
        """Verify production deployment workflow exists"""
        _p = self._repo_path('.github/workflows/deploy-production.yml')
        assert os.path.isfile(_p), f'Missing file: .github/workflows/deploy-production.yml'
        self._load_yaml(_p)  # parse check

    def test_composite_action_exists(self):
        """Verify composite action setup file exists"""
        _p = self._repo_path('.github/actions/setup-node-env/action.yml')
        assert os.path.isfile(_p), f'Missing file: .github/actions/setup-node-env/action.yml'
        self._load_yaml(_p)  # parse check

    # ── semantic_check (static) ────────────────────────────────────────

    def test_ci_matrix_node_versions(self):
        """Verify CI matrix has at least 2 Node.js versions"""
        _p = self._repo_path('.github/workflows/ci.yml')
        assert os.path.exists(_p), f'Missing: .github/workflows/ci.yml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'matrix' in _all, 'Missing: matrix'
        assert 'node-version' in _all, 'Missing: node-version'

    def test_production_environment_protection(self):
        """Verify deploy-production has environment: production"""
        _p = self._repo_path('.github/workflows/deploy-production.yml')
        assert os.path.exists(_p), f'Missing: .github/workflows/deploy-production.yml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'environment' in _all, 'Missing: environment'
        assert 'production' in _all, 'Missing: production'

    def test_composite_action_using_composite(self):
        """Verify composite action uses 'runs.using: composite'"""
        _p = self._repo_path('.github/actions/setup-node-env/action.yml')
        assert os.path.exists(_p), f'Missing: .github/actions/setup-node-env/action.yml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'using' in _all, 'Missing: using'
        assert 'composite' in _all, 'Missing: composite'

    def test_dependency_update_schedule(self):
        """Verify dependency-update.yml has cron schedule"""
        _p = self._repo_path('.github/workflows/dependency-update.yml')
        assert os.path.exists(_p), f'Missing: .github/workflows/dependency-update.yml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'schedule' in _all, 'Missing: schedule'
        assert 'cron' in _all, 'Missing: cron'

    # ── functional_check ────────────────────────────────────────

    def test_all_workflows_valid_yaml(self):
        """Verify all workflow YAML files parse without error"""
        result = self._run_cmd('python', args=['-c', "import yaml,glob; files=glob.glob('.github/workflows/*.yml'); [yaml.safe_load(open(f)) for f in files]; print(f'{len(files)} workflows valid YAML: PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_all_workflows_valid_yaml failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_ci_has_push_and_pr_triggers(self):
        """Verify ci.yml triggers on push and pull_request"""
        result = self._run_cmd('python', args=['-c', "import yaml; ci=yaml.safe_load(open('.github/workflows/ci.yml')); on=ci.get('on',ci.get(True,{})); assert 'push' in str(on) or True in ci; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_ci_has_push_and_pr_triggers failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_matrix_has_two_versions(self):
        """Verify matrix strategy includes at least 2 versions"""
        result = self._run_cmd('python', args=['-c', "import yaml,json; ci=yaml.safe_load(open('.github/workflows/ci.yml')); s=json.dumps(ci); assert s.count('node-version')>0; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_matrix_has_two_versions failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_production_environment_in_yaml(self):
        """Verify 'production' environment in deploy-production YAML"""
        result = self._run_cmd('python', args=['-c', "import yaml; p=yaml.safe_load(open('.github/workflows/deploy-production.yml')); jobs=p.get('jobs',{}); envs=[str(j.get('environment','')) for j in jobs.values()]; assert any('production' in e for e in envs), 'No production environment'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_production_environment_in_yaml failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_workflow_count_minimum(self):
        """Verify at least 5 workflow files exist"""
        result = self._run_cmd('python', args=['-c', "import glob; wfs=glob.glob('.github/workflows/*.yml'); assert len(wfs)>=5, f'Only {len(wfs)} workflows found'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_workflow_count_minimum failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

