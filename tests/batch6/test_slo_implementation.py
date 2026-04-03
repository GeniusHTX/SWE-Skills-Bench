"""
Tests for 'slo-implementation' skill.
Generated from benchmark case definitions for slo-implementation.
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


class TestSloImplementation:
    """Verify the slo-implementation skill output."""

    REPO_DIR = '/workspace/slo-generator'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestSloImplementation.REPO_DIR, rel)

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

    def test_recording_rules_exist(self):
        """Verify recording rules YAML exists"""
        _p = self._repo_path('slo/prometheus/recording-rules.yaml')
        assert os.path.isfile(_p), f'Missing file: slo/prometheus/recording-rules.yaml'
        self._load_yaml(_p)  # parse check

    def test_alerting_rules_exist(self):
        """Verify alerting rules YAML exists"""
        _p = self._repo_path('slo/prometheus/alerting-rules.yaml')
        assert os.path.isfile(_p), f'Missing file: slo/prometheus/alerting-rules.yaml'
        self._load_yaml(_p)  # parse check

    # ── semantic_check (static) ────────────────────────────────────────

    def test_recording_rules_slo_prefix(self):
        """Verify all recording rule names start with 'slo:' prefix"""
        _p = self._repo_path('slo/prometheus/recording-rules.yaml')
        assert os.path.exists(_p), f'Missing: slo/prometheus/recording-rules.yaml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'record' in _all, 'Missing: record'
        assert 'slo:' in _all, 'Missing: slo:'
        assert 'expr' in _all, 'Missing: expr'

    def test_multi_window_burn_rate_alerts(self):
        """Verify at least 2 burn rate alert windows (fast/slow)"""
        _p = self._repo_path('slo/prometheus/alerting-rules.yaml')
        assert os.path.exists(_p), f'Missing: slo/prometheus/alerting-rules.yaml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'alert' in _all, 'Missing: alert'
        assert 'expr' in _all, 'Missing: expr'
        assert '1h' in _all, 'Missing: 1h'
        assert '6h' in _all, 'Missing: 6h'
        assert 'burn' in _all, 'Missing: burn'
        assert 'rate' in _all, 'Missing: rate'

    def test_alert_severity_labels(self):
        """Verify alerts have severity: critical or warning labels"""
        _p = self._repo_path('slo/prometheus/alerting-rules.yaml')
        assert os.path.exists(_p), f'Missing: slo/prometheus/alerting-rules.yaml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'severity' in _all, 'Missing: severity'
        assert 'critical' in _all, 'Missing: critical'
        assert 'warning' in _all, 'Missing: warning'
        assert 'labels' in _all, 'Missing: labels'

    def test_alerts_have_for_duration(self):
        """Verify all alerts have 'for' duration to prevent flapping"""
        _p = self._repo_path('slo/prometheus/alerting-rules.yaml')
        assert os.path.exists(_p), f'Missing: slo/prometheus/alerting-rules.yaml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'for' in _all, 'Missing: for'
        assert 'annotations' in _all, 'Missing: annotations'
        assert 'summary' in _all, 'Missing: summary'

    # ── functional_check ────────────────────────────────────────

    def test_recording_rules_yaml_valid(self):
        """Verify recording rules YAML parses correctly"""
        self._ensure_setup('test_recording_rules_yaml_valid', ['pip install pyyaml'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import yaml; data=yaml.safe_load(open('slo/prometheus/recording-rules.yaml')); assert 'groups' in data; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_recording_rules_yaml_valid failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_record_names_start_with_slo(self):
        """Verify all record names follow slo: prefix convention"""
        self._ensure_setup('test_record_names_start_with_slo', ['pip install pyyaml'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import yaml; data=yaml.safe_load(open('slo/prometheus/recording-rules.yaml')); rules=[r for g in data['groups'] for r in g['rules']]; assert all(r['record'].startswith('slo:') for r in rules if 'record' in r); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_record_names_start_with_slo failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_alerting_rules_yaml_valid(self):
        """Verify alerting rules YAML parses correctly"""
        self._ensure_setup('test_alerting_rules_yaml_valid', ['pip install pyyaml'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import yaml; data=yaml.safe_load(open('slo/prometheus/alerting-rules.yaml')); assert 'groups' in data; alerts=[a for g in data['groups'] for a in g['rules']]; assert len(alerts)>=2; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_alerting_rules_yaml_valid failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_alerts_have_for_key(self):
        """Verify all alerts have 'for' key programmatically"""
        self._ensure_setup('test_alerts_have_for_key', ['pip install pyyaml'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import yaml; data=yaml.safe_load(open('slo/prometheus/alerting-rules.yaml')); alerts=[a for g in data['groups'] for a in g['rules']]; assert all('for' in a for a in alerts); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_alerts_have_for_key failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_severity_labels_valid(self):
        """Verify severity labels are critical or warning"""
        self._ensure_setup('test_severity_labels_valid', ['pip install pyyaml'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import yaml; data=yaml.safe_load(open('slo/prometheus/alerting-rules.yaml')); alerts=[a for g in data['groups'] for a in g['rules']]; assert all(a.get('labels',{}).get('severity') in ('critical','warning') for a in alerts); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_severity_labels_valid failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_invalid_prefix_detection(self):
        """Verify non-slo: prefix would fail validation"""
        self._ensure_setup('test_invalid_prefix_detection', ['pip install pyyaml'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "rules=[{'record':'job:error_rate','expr':'1'}]; assert not all(r['record'].startswith('slo:') for r in rules); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_invalid_prefix_detection failed (exit {result.returncode})\n' + result.stderr[:500]
        )

