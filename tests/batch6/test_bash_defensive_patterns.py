"""
Tests for 'bash-defensive-patterns' skill.
Generated from benchmark case definitions for bash-defensive-patterns.
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


class TestBashDefensivePatterns:
    """Verify the bash-defensive-patterns skill output."""

    REPO_DIR = '/workspace/shellcheck'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestBashDefensivePatterns.REPO_DIR, rel)

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

    def test_deploy_sh_exists(self):
        """Verify deploy.sh script exists"""
        _p = self._repo_path('scripts/deploy.sh')
        assert os.path.isfile(_p), f'Missing file: scripts/deploy.sh'

    def test_health_check_sh_exists(self):
        """Verify health-check.sh script exists"""
        _p = self._repo_path('scripts/health-check.sh')
        assert os.path.isfile(_p), f'Missing file: scripts/health-check.sh'

    def test_common_sh_exists(self):
        """Verify shared utility library exists"""
        _p = self._repo_path('lib/common.sh')
        assert os.path.isfile(_p), f'Missing file: lib/common.sh'

    # ── semantic_check (static) ────────────────────────────────────────

    def test_set_euo_pipefail_in_deploy(self):
        """Verify deploy.sh starts with set -euo pipefail"""
        _p = self._repo_path('scripts/deploy.sh')
        assert os.path.exists(_p), f'Missing: scripts/deploy.sh'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'set -euo pipefail' in _all, 'Missing: set -euo pipefail'

    def test_trap_err_in_deploy(self):
        """Verify deploy.sh has trap ERR handler for failure cleanup"""
        _p = self._repo_path('scripts/deploy.sh')
        assert os.path.exists(_p), f'Missing: scripts/deploy.sh'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'trap' in _all, 'Missing: trap'
        assert 'ERR' in _all, 'Missing: ERR'

    def test_dry_run_flag_parsing(self):
        """Verify deploy.sh has --dry-run argument parsing"""
        _p = self._repo_path('scripts/deploy.sh')
        assert os.path.exists(_p), f'Missing: scripts/deploy.sh'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'dry-run' in _all, 'Missing: dry-run'
        assert 'getopts' in _all, 'Missing: getopts'
        assert 'case' in _all, 'Missing: case'
        assert '--dry-run' in _all, 'Missing: --dry-run'

    def test_common_sh_log_function(self):
        """Verify common.sh defines log() and error() functions"""
        _p = self._repo_path('lib/common.sh')
        assert os.path.exists(_p), f'Missing: lib/common.sh'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert re.search('log()', _all, re.MULTILINE), 'Pattern not found: log()'
        assert re.search('error()', _all, re.MULTILINE), 'Pattern not found: error()'
        assert 'require_env' in _all, 'Missing: require_env'

    # ── functional_check ────────────────────────────────────────

    def test_deploy_syntax_check(self):
        """Verify deploy.sh passes bash syntax check"""
        result = self._run_cmd('bash', args=['-n', 'scripts/deploy.sh'], timeout=120)
        assert result.returncode == 0, (
            f'test_deploy_syntax_check failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_health_check_syntax_check(self):
        """Verify health-check.sh passes bash syntax check"""
        result = self._run_cmd('bash', args=['-n', 'scripts/health-check.sh'], timeout=120)
        assert result.returncode == 0, (
            f'test_health_check_syntax_check failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_rollback_syntax_check(self):
        """Verify rollback.sh passes bash syntax check"""
        result = self._run_cmd('bash', args=['-n', 'scripts/rollback.sh'], timeout=120)
        assert result.returncode == 0, (
            f'test_rollback_syntax_check failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_deploy_dry_run_exit_zero(self):
        """Verify deploy.sh --dry-run exits 0 without making real changes"""
        result = self._run_cmd('bash', args=['scripts/deploy.sh', '--dry-run'], timeout=120)
        assert result.returncode == 0, (
            f'test_deploy_dry_run_exit_zero failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_health_check_retry_loop_present(self):
        """Verify health-check.sh has parameterized retry loop with --max-retries"""
        _p = self._repo_path('scripts/health-check.sh')
        assert os.path.exists(_p), f'Missing: scripts/health-check.sh'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'max-retries' in _all, 'Missing: max-retries'
        assert 'interval' in _all, 'Missing: interval'
        assert 'while' in _all, 'Missing: while'
        assert 'sleep' in _all, 'Missing: sleep'
        assert 'curl' in _all, 'Missing: curl'

