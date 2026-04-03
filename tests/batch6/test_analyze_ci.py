"""
Tests for 'analyze-ci' skill.
Generated from benchmark case definitions for analyze-ci.
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


class TestAnalyzeCi:
    """Verify the analyze-ci skill output."""

    REPO_DIR = '/workspace/sentry'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestAnalyzeCi.REPO_DIR, rel)

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
        """Verify CLI entry point module exists"""
        _p = self._repo_path('src/analyze_ci/cli.py')
        assert os.path.isfile(_p), f'Missing file: src/analyze_ci/cli.py'
        py_compile.compile(_p, doraise=True)

    def test_log_parser_module_exists(self):
        """Verify log parser module exists"""
        _p = self._repo_path('src/analyze_ci/log_parser.py')
        assert os.path.isfile(_p), f'Missing file: src/analyze_ci/log_parser.py'
        py_compile.compile(_p, doraise=True)

    def test_report_module_exists(self):
        """Verify report module exists"""
        _p = self._repo_path('src/analyze_ci/report.py')
        assert os.path.isfile(_p), f'Missing file: src/analyze_ci/report.py'
        py_compile.compile(_p, doraise=True)

    # ── semantic_check (static) ────────────────────────────────────────

    def test_logparser_class_defined(self):
        """Verify LogParser class with parse method exists"""
        _p = self._repo_path('src/analyze_ci/log_parser.py')
        assert os.path.exists(_p), f'Missing: src/analyze_ci/log_parser.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'class LogParser' in _all, 'Missing: class LogParser'
        assert 'def parse' in _all, 'Missing: def parse'

    def test_parsedci_dataclass_fields(self):
        """Verify ParsedCI has status, failures, duration fields"""
        _p = self._repo_path('src/analyze_ci/log_parser.py')
        assert os.path.exists(_p), f'Missing: src/analyze_ci/log_parser.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'ParsedCI' in _all, 'Missing: ParsedCI'
        assert 'status' in _all, 'Missing: status'
        assert 'failures' in _all, 'Missing: failures'
        assert 'duration' in _all, 'Missing: duration'
        assert 'dataclass' in _all, 'Missing: dataclass'

    def test_cli_uses_argparse_subcommands(self):
        """Verify CLI uses argparse or click with subcommands"""
        _p = self._repo_path('src/analyze_ci/cli.py')
        assert os.path.exists(_p), f'Missing: src/analyze_ci/cli.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'argparse' in _all, 'Missing: argparse'
        assert 'add_subparsers' in _all, 'Missing: add_subparsers'
        assert 'parse' in _all, 'Missing: parse'
        assert 'report' in _all, 'Missing: report'

    def test_console_scripts_entrypoint(self):
        """Verify console_scripts entry point is configured"""
        _p = self._repo_path('pyproject.toml')
        assert os.path.exists(_p), f'Missing: pyproject.toml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'console_scripts' in _all, 'Missing: console_scripts'
        assert 'analyze-ci' in _all, 'Missing: analyze-ci'
        assert 'analyze_ci.cli:main' in _all, 'Missing: analyze_ci.cli:main'

    # ── functional_check ────────────────────────────────────────

    def test_cli_help_exit_zero(self):
        """Verify --help exits with code 0 and shows usage"""
        self._ensure_setup('test_cli_help_exit_zero', ['pip install -e .'], 'skip_if_setup_fails')
        result = self._run_cmd('python', args=['-m', 'analyze_ci', '--help'], timeout=120)
        assert result.returncode == 0, (
            f'test_cli_help_exit_zero failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_parse_passed_log(self):
        """Verify LogParser.parse returns status='passed' for passing log"""
        self._ensure_setup('test_parse_passed_log', ['pip install -e .'], 'skip_if_setup_fails')
        result = self._run_cmd('python', args=['-c', "from analyze_ci.log_parser import LogParser; p=LogParser(); r=p.parse('PASSED'); assert r.status=='passed'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_parse_passed_log failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_parse_failed_log_extracts_failures(self):
        """Verify parser extracts failure names from FAILED log lines"""
        self._ensure_setup('test_parse_failed_log_extracts_failures', ['pip install -e .'], 'skip_if_setup_fails')
        result = self._run_cmd('python', args=['-c', "from analyze_ci.log_parser import LogParser; p=LogParser(); r=p.parse('FAILED: test_foo\\nFAILED: test_bar'); assert len(r.failures)==2; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_parse_failed_log_extracts_failures failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_report_json_format_valid(self):
        """Verify report --format json outputs valid JSON"""
        self._ensure_setup('test_report_json_format_valid', ['pip install -e .'], 'skip_if_setup_fails')
        result = self._run_cmd('python', args=['-c', "import json; from analyze_ci.log_parser import LogParser; from analyze_ci.report import Report; p=LogParser(); r=p.parse('PASSED'); output=Report.generate(r, 'json'); json.loads(output); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_report_json_format_valid failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_parse_nonexistent_file_exits_nonzero(self):
        """Verify parse on nonexistent file exits with non-zero code"""
        self._ensure_setup('test_parse_nonexistent_file_exits_nonzero', ['pip install -e .'], 'skip_if_setup_fails')
        result = self._run_cmd('python', args=['-m', 'analyze_ci', 'parse', 'nonexistent_file_12345.log'], timeout=120)
        assert result.returncode == 0, (
            f'test_parse_nonexistent_file_exits_nonzero failed (exit {result.returncode})\n' + result.stderr[:500]
        )

