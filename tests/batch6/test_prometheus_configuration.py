"""
Tests for 'prometheus-configuration' skill.
Generated from benchmark case definitions for prometheus-configuration.
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


class TestPrometheusConfiguration:
    """Verify the prometheus-configuration skill output."""

    REPO_DIR = '/workspace/prometheus'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestPrometheusConfiguration.REPO_DIR, rel)

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

    def test_prometheus_yml_exists(self):
        """Verify prometheus.yml and rules files exist"""
        _p = self._repo_path('monitoring/prometheus/prometheus.yml')
        assert os.path.isfile(_p), f'Missing file: monitoring/prometheus/prometheus.yml'
        self._load_yaml(_p)  # parse check
        _p = self._repo_path('monitoring/prometheus/recording-rules.yml')
        assert os.path.isfile(_p), f'Missing file: monitoring/prometheus/recording-rules.yml'
        self._load_yaml(_p)  # parse check
        _p = self._repo_path('monitoring/prometheus/alerting-rules.yml')
        assert os.path.isfile(_p), f'Missing file: monitoring/prometheus/alerting-rules.yml'
        self._load_yaml(_p)  # parse check

    def test_alertmanager_yml_exists(self):
        """Verify alertmanager.yml exists"""
        _p = self._repo_path('monitoring/alertmanager/alertmanager.yml')
        assert os.path.isfile(_p), f'Missing file: monitoring/alertmanager/alertmanager.yml'
        self._load_yaml(_p)  # parse check

    # ── semantic_check (static) ────────────────────────────────────────

    def test_prometheus_has_global_and_scrape(self):
        """Verify prometheus.yml has global and scrape_configs keys"""
        _p = self._repo_path('monitoring/prometheus/prometheus.yml')
        assert os.path.exists(_p), f'Missing: monitoring/prometheus/prometheus.yml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'global' in _all, 'Missing: global'
        assert 'scrape_configs' in _all, 'Missing: scrape_configs'

    def test_recording_rules_has_record(self):
        """Verify recording-rules.yml has groups with record entries"""
        _p = self._repo_path('monitoring/prometheus/recording-rules.yml')
        assert os.path.exists(_p), f'Missing: monitoring/prometheus/recording-rules.yml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'groups' in _all, 'Missing: groups'
        assert 'record' in _all, 'Missing: record'

    def test_alerting_rules_has_alert(self):
        """Verify alerting-rules.yml has alert definitions with expr and for"""
        _p = self._repo_path('monitoring/prometheus/alerting-rules.yml')
        assert os.path.exists(_p), f'Missing: monitoring/prometheus/alerting-rules.yml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'alert' in _all, 'Missing: alert'
        assert 'expr' in _all, 'Missing: expr'
        assert 'for' in _all, 'Missing: for'

    def test_alertmanager_has_receivers(self):
        """Verify alertmanager.yml has route and receivers keys"""
        _p = self._repo_path('monitoring/alertmanager/alertmanager.yml')
        assert os.path.exists(_p), f'Missing: monitoring/alertmanager/alertmanager.yml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'route' in _all, 'Missing: route'
        assert 'receivers' in _all, 'Missing: receivers'

    # ── functional_check ────────────────────────────────────────

    def test_all_yaml_parseable(self):
        """Verify all Prometheus YAML files parse without error"""
        result = self._run_cmd('python', args=['-c', "import yaml; [yaml.safe_load(open(f)) for f in ['monitoring/prometheus/prometheus.yml','monitoring/prometheus/recording-rules.yml','monitoring/prometheus/alerting-rules.yml','monitoring/alertmanager/alertmanager.yml']]; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_all_yaml_parseable failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_scrape_jobs_count(self):
        """Verify at least 3 scrape jobs defined"""
        result = self._run_cmd('python', args=['-c', "import yaml; config=yaml.safe_load(open('monitoring/prometheus/prometheus.yml')); jobs=config['scrape_configs']; assert len(jobs)>=3, f'Only {len(jobs)} scrape jobs'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_scrape_jobs_count failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_recording_rules_count(self):
        """Verify at least 2 recording rules exist"""
        result = self._run_cmd('python', args=['-c', "import yaml; rules=yaml.safe_load(open('monitoring/prometheus/recording-rules.yml')); records=[r for g in rules['groups'] for r in g['rules'] if 'record' in r]; assert len(records)>=2, f'Only {len(records)} recording rules'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_recording_rules_count failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_alert_rules_count(self):
        """Verify at least 3 alert rules defined"""
        result = self._run_cmd('python', args=['-c', "import yaml; a=yaml.safe_load(open('monitoring/prometheus/alerting-rules.yml')); alerts=[r for g in a['groups'] for r in g['rules'] if 'alert' in r]; assert len(alerts)>=3, f'Only {len(alerts)} alerts'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_alert_rules_count failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_alertmanager_receivers_nonempty(self):
        """Verify alertmanager has at least one receiver"""
        result = self._run_cmd('python', args=['-c', "import yaml; am=yaml.safe_load(open('monitoring/alertmanager/alertmanager.yml')); assert len(am.get('receivers',[]))>=1, 'No receivers'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_alertmanager_receivers_nonempty failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_unique_job_names(self):
        """Verify all scrape job_names are unique"""
        result = self._run_cmd('python', args=['-c', "import yaml; config=yaml.safe_load(open('monitoring/prometheus/prometheus.yml')); names=[j['job_name'] for j in config['scrape_configs']]; assert len(set(names))==len(names), f'Duplicate job names: {names}'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_unique_job_names failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

