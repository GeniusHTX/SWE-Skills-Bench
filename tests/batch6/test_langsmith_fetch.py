"""
Tests for 'langsmith-fetch' skill.
Generated from benchmark case definitions for langsmith-fetch.
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


class TestLangsmithFetch:
    """Verify the langsmith-fetch skill output."""

    REPO_DIR = '/workspace/langchain'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestLangsmithFetch.REPO_DIR, rel)

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

    def test_debug_agent_sh_exists(self):
        """Verify debug_agent.sh script exists"""
        _p = self._repo_path('scripts/debug_agent.sh')
        assert os.path.isfile(_p), f'Missing file: scripts/debug_agent.sh'

    def test_analyze_traces_py_exists(self):
        """Verify analyze_traces.py script exists"""
        _p = self._repo_path('scripts/analyze_traces.py')
        assert os.path.isfile(_p), f'Missing file: scripts/analyze_traces.py'
        py_compile.compile(_p, doraise=True)

    # ── semantic_check (static) ────────────────────────────────────────

    def test_bash_shebang_line(self):
        """Verify debug_agent.sh has proper shebang"""
        _p = self._repo_path('scripts/debug_agent.sh')
        assert os.path.exists(_p), f'Missing: scripts/debug_agent.sh'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert '#!/bin/bash' in _all, 'Missing: #!/bin/bash'
        assert '#!/usr/bin/env bash' in _all, 'Missing: #!/usr/bin/env bash'

    def test_bash_api_key_check(self):
        """Verify debug_agent.sh checks for LANGCHAIN_API_KEY"""
        _p = self._repo_path('scripts/debug_agent.sh')
        assert os.path.exists(_p), f'Missing: scripts/debug_agent.sh'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'LANGCHAIN_API_KEY' in _all, 'Missing: LANGCHAIN_API_KEY'

    def test_python_argparse_arguments(self):
        """Verify analyze_traces.py has --project, --since, --output arguments"""
        _p = self._repo_path('scripts/analyze_traces.py')
        assert os.path.exists(_p), f'Missing: scripts/analyze_traces.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'argparse' in _all, 'Missing: argparse'
        assert '--project' in _all, 'Missing: --project'
        assert '--since' in _all, 'Missing: --since'
        assert '--output' in _all, 'Missing: --output'

    def test_python_uses_auth_header(self):
        """Verify API key sent via Authorization header not query param"""
        _p = self._repo_path('scripts/analyze_traces.py')
        assert os.path.exists(_p), f'Missing: scripts/analyze_traces.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'Authorization' in _all, 'Missing: Authorization'
        assert 'Bearer' in _all, 'Missing: Bearer'
        assert 'headers' in _all, 'Missing: headers'

    # ── functional_check ────────────────────────────────────────

    def test_python_help_exits_zero(self):
        """Verify analyze_traces.py --help exits 0"""
        self._ensure_setup('test_python_help_exits_zero', ['pip install langsmith requests'], 'fail_if_missing')
        result = self._run_cmd('python', args=['scripts/analyze_traces.py', '--help'], timeout=120)
        assert result.returncode == 0, (
            f'test_python_help_exits_zero failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_bash_missing_api_key_exit_1(self):
        """Verify debug_agent.sh exits 1 when LANGCHAIN_API_KEY unset"""
        result = self._run_cmd('bash', args=['-c', 'unset LANGCHAIN_API_KEY; bash scripts/debug_agent.sh; echo EXIT:$?'], timeout=120)
        assert result.returncode == 1, (
            f'test_bash_missing_api_key_exit_1 failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_csv_output_valid(self):
        """Verify CSV output has header row with expected columns"""
        self._ensure_setup('test_csv_output_valid', ['pip install langsmith requests'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import subprocess,csv,io; result=subprocess.run(['python','scripts/analyze_traces.py','--output','/dev/stdout','--since','0'],capture_output=True,text=True,env={**__import__('os').environ,'LANGCHAIN_API_KEY':'test'}); reader=csv.reader(io.StringIO(result.stdout)); headers=next(reader,[]); assert len(headers)>=3; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_csv_output_valid failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_bash_help_exits_zero(self):
        """Verify debug_agent.sh --help exits 0"""
        result = self._run_cmd('bash', args=['scripts/debug_agent.sh', '--help'], timeout=120)
        assert result.returncode == 0, (
            f'test_bash_help_exits_zero failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_python_syntax_check(self):
        """Verify analyze_traces.py has no syntax errors"""
        result = self._run_cmd('python', args=['-c', "import py_compile; py_compile.compile('scripts/analyze_traces.py', doraise=True); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_python_syntax_check failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_bash_no_hardcoded_key(self):
        """Verify debug_agent.sh does not hardcode API keys"""
        result = self._run_cmd('python', args=['-c', "content=open('scripts/debug_agent.sh').read(); assert 'lsv2_' not in content.lower() and 'sk-' not in content, 'Hardcoded API key found'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_bash_no_hardcoded_key failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

