"""
Tests for 'python-performance-optimization' skill.
Generated from benchmark case definitions for python-performance-optimization.
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


class TestPythonPerformanceOptimization:
    """Verify the python-performance-optimization skill output."""

    REPO_DIR = '/workspace/py-spy'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestPythonPerformanceOptimization.REPO_DIR, rel)

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

    def test_profile_scripts_exist(self):
        """Verify all 3 profiling scripts exist"""
        _p = self._repo_path('scripts/profile_aggregator.py')
        assert os.path.isfile(_p), f'Missing file: scripts/profile_aggregator.py'
        py_compile.compile(_p, doraise=True)
        _p = self._repo_path('scripts/flamegraph_filter.py')
        assert os.path.isfile(_p), f'Missing file: scripts/flamegraph_filter.py'
        py_compile.compile(_p, doraise=True)
        _p = self._repo_path('scripts/profile_report.py')
        assert os.path.isfile(_p), f'Missing file: scripts/profile_report.py'
        py_compile.compile(_p, doraise=True)

    def test_test_file_exists(self):
        """Verify test file exists"""
        _p = self._repo_path('tests/test_profiling_scripts.py')
        assert os.path.isfile(_p), f'Missing file: tests/test_profiling_scripts.py'
        py_compile.compile(_p, doraise=True)

    # ── semantic_check (static) ────────────────────────────────────────

    def test_argparse_in_all_scripts(self):
        """Verify all scripts use argparse for CLI interface"""
        _p = self._repo_path('scripts/profile_aggregator.py')
        assert os.path.exists(_p), f'Missing: scripts/profile_aggregator.py'
        _contents = self._safe_read(_p)
        _p = self._repo_path('scripts/profile_report.py')
        assert os.path.exists(_p), f'Missing: scripts/profile_report.py'
        _contents = self._safe_read(_p)
        _p = self._repo_path('scripts/flamegraph_filter.py')
        assert os.path.exists(_p), f'Missing: scripts/flamegraph_filter.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'argparse' in _all, 'Missing: argparse'
        assert 'ArgumentParser' in _all, 'Missing: ArgumentParser'
        assert 'add_argument' in _all, 'Missing: add_argument'

    def test_pstats_usage_in_aggregator(self):
        """Verify profile_aggregator uses pstats.Stats for aggregation"""
        _p = self._repo_path('scripts/profile_aggregator.py')
        assert os.path.exists(_p), f'Missing: scripts/profile_aggregator.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'pstats' in _all, 'Missing: pstats'
        assert 'Stats' in _all, 'Missing: Stats'
        assert 'add' in _all, 'Missing: add'
        assert 'dump_stats' in _all, 'Missing: dump_stats'

    def test_svg_parsing_in_filter(self):
        """Verify flamegraph_filter uses XML/regex to parse SVG"""
        _p = self._repo_path('scripts/flamegraph_filter.py')
        assert os.path.exists(_p), f'Missing: scripts/flamegraph_filter.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'ElementTree' in _all, 'Missing: ElementTree'
        assert 'xml.etree' in _all, 'Missing: xml.etree'
        assert 're.search' in _all, 'Missing: re.search'
        assert 'svg' in _all, 'Missing: svg'

    # ── functional_check ────────────────────────────────────────

    def test_all_scripts_help(self):
        """Verify all 3 scripts respond to --help with exit code 0"""
        result = self._run_cmd('python', args=['-c', "import subprocess; scripts=['scripts/profile_aggregator.py','scripts/profile_report.py','scripts/flamegraph_filter.py']; [subprocess.run(['python',s,'--help'],check=True,capture_output=True) for s in scripts]; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_all_scripts_help failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_report_on_synthetic_prof(self):
        """Verify profile_report generates output from synthetic .prof"""
        self._ensure_setup('test_report_on_synthetic_prof', ['pip install pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import cProfile, tempfile, os, subprocess; f=tempfile.NamedTemporaryFile(suffix='.prof',delete=False); cProfile.run('sum(range(1000))',f.name); r=subprocess.run(['python','scripts/profile_report.py','--input',f.name,'--format','text','--top','5'],capture_output=True,text=True); os.unlink(f.name); assert r.returncode==0; assert len(r.stdout.strip())>0; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_report_on_synthetic_prof failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_aggregator_merges_two_files(self):
        """Verify profile_aggregator merges 2 .prof files into output"""
        result = self._run_cmd('python', args=['-c', "import cProfile, tempfile, os, subprocess; a=tempfile.NamedTemporaryFile(suffix='.prof',delete=False); b=tempfile.NamedTemporaryFile(suffix='.prof',delete=False); out=tempfile.NamedTemporaryFile(suffix='.prof',delete=False); cProfile.run('sum(range(100))',a.name); cProfile.run('list(range(100))',b.name); r=subprocess.run(['python','scripts/profile_aggregator.py','--input',a.name,b.name,'--output',out.name]); assert r.returncode==0; assert os.path.getsize(out.name)>0; [os.unlink(f) for f in [a.name,b.name,out.name]]; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_aggregator_merges_two_files failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_report_top_n_limiting(self):
        """Verify --top flag limits output rows"""
        result = self._run_cmd('python', args=['-c', "import cProfile, tempfile, os, subprocess; f=tempfile.NamedTemporaryFile(suffix='.prof',delete=False); cProfile.run('sum(range(1000))',f.name); r=subprocess.run(['python','scripts/profile_report.py','--input',f.name,'--format','text','--top','3'],capture_output=True,text=True); os.unlink(f.name); lines=[l for l in r.stdout.strip().split('\\n') if l.strip()]; assert len([l for l in lines if 'function' not in l.lower() and 'ncalls' not in l.lower()])<=5; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_report_top_n_limiting failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_aggregator_single_file_passthrough(self):
        """Verify single file aggregation produces identical output"""
        result = self._run_cmd('python', args=['-c', "import cProfile, tempfile, os, subprocess; a=tempfile.NamedTemporaryFile(suffix='.prof',delete=False); out=tempfile.NamedTemporaryFile(suffix='.prof',delete=False); cProfile.run('sum(range(100))',a.name); r=subprocess.run(['python','scripts/profile_aggregator.py','--input',a.name,'--output',out.name]); assert r.returncode==0; assert os.path.getsize(out.name)>0; [os.unlink(f) for f in [a.name,out.name]]; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_aggregator_single_file_passthrough failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_nonexistent_prof_file_error(self):
        """Verify missing .prof file gives FileNotFoundError"""
        result = self._run_cmd('python', args=['-c', "import subprocess; r=subprocess.run(['python','scripts/profile_report.py','--input','nonexistent.prof'],capture_output=True,text=True); assert r.returncode!=0; assert 'error' in r.stderr.lower() or 'not found' in r.stderr.lower() or 'FileNotFoundError' in r.stderr; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_nonexistent_prof_file_error failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_full_profiling_suite(self):
        """Run the full profiling scripts test suite"""
        self._ensure_setup('test_full_profiling_suite', ['pip install pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_profiling_scripts.py', '-v', '--tb=short'], timeout=120)
        assert result.returncode == 0, (
            f'test_full_profiling_suite failed (exit {result.returncode})\n' + result.stderr[:500]
        )

