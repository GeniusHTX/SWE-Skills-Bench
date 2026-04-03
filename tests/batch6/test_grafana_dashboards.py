"""
Tests for 'grafana-dashboards' skill.
Generated from benchmark case definitions for grafana-dashboards.
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


class TestGrafanaDashboards:
    """Verify the grafana-dashboards skill output."""

    REPO_DIR = '/workspace/grafana'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestGrafanaDashboards.REPO_DIR, rel)

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

    def test_dashboard_json_files_exist(self):
        """Verify all 3 dashboard JSON files exist"""
        _p = self._repo_path('monitoring/grafana/dashboards/infrastructure-overview.json')
        assert os.path.isfile(_p), f'Missing file: monitoring/grafana/dashboards/infrastructure-overview.json'
        self._load_json(_p)  # parse check
        _p = self._repo_path('monitoring/grafana/dashboards/application-metrics.json')
        assert os.path.isfile(_p), f'Missing file: monitoring/grafana/dashboards/application-metrics.json'
        self._load_json(_p)  # parse check
        _p = self._repo_path('monitoring/grafana/dashboards/slo-tracking.json')
        assert os.path.isfile(_p), f'Missing file: monitoring/grafana/dashboards/slo-tracking.json'
        self._load_json(_p)  # parse check

    def test_provisioning_yaml_exists(self):
        """Verify provisioning YAML file exists"""
        _p = self._repo_path('monitoring/grafana/provisioning/dashboards.yml')
        assert os.path.isfile(_p), f'Missing file: monitoring/grafana/provisioning/dashboards.yml'
        self._load_yaml(_p)  # parse check

    # ── semantic_check (static) ────────────────────────────────────────

    def test_dashboard_has_uid_and_panels(self):
        """Verify each dashboard JSON has uid, title, and panels keys"""
        _p = self._repo_path('monitoring/grafana/dashboards/infrastructure-overview.json')
        assert os.path.exists(_p), f'Missing: monitoring/grafana/dashboards/infrastructure-overview.json'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'uid' in _all, 'Missing: uid'
        assert 'title' in _all, 'Missing: title'
        assert 'panels' in _all, 'Missing: panels'

    def test_infrastructure_has_node_metrics(self):
        """Verify infrastructure dashboard references node_cpu or node_memory metrics"""
        _p = self._repo_path('monitoring/grafana/dashboards/infrastructure-overview.json')
        assert os.path.exists(_p), f'Missing: monitoring/grafana/dashboards/infrastructure-overview.json'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'node_cpu' in _all, 'Missing: node_cpu'
        assert 'node_memory' in _all, 'Missing: node_memory'

    def test_application_metrics_has_rate(self):
        """Verify application-metrics dashboard has rate() in at least one panel"""
        _p = self._repo_path('monitoring/grafana/dashboards/application-metrics.json')
        assert os.path.exists(_p), f'Missing: monitoring/grafana/dashboards/application-metrics.json'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert re.search('rate(', _all, re.MULTILINE), 'Pattern not found: rate('

    def test_slo_has_burn_rate_or_error_budget(self):
        """Verify slo-tracking has burn_rate or error_budget references"""
        _p = self._repo_path('monitoring/grafana/dashboards/slo-tracking.json')
        assert os.path.exists(_p), f'Missing: monitoring/grafana/dashboards/slo-tracking.json'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'burn_rate' in _all, 'Missing: burn_rate'
        assert 'error_budget' in _all, 'Missing: error_budget'

    # ── functional_check ────────────────────────────────────────

    def test_all_dashboards_valid_json(self):
        """Verify all 3 dashboard files are valid JSON"""
        result = self._run_cmd('python', args=['-c', "import json,glob; files=glob.glob('monitoring/grafana/dashboards/*.json'); assert len(files)>=3; [json.loads(open(f).read()) for f in files]; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_all_dashboards_valid_json failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_uid_uniqueness(self):
        """Verify all dashboard uids are unique"""
        result = self._run_cmd('python', args=['-c', "import json,glob; files=glob.glob('monitoring/grafana/dashboards/*.json'); uids=[json.loads(open(f).read())['uid'] for f in files]; assert len(set(uids))==len(uids), f'Duplicate uids: {uids}'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_uid_uniqueness failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_panels_count_minimum(self):
        """Verify each dashboard has at least 3 panels"""
        result = self._run_cmd('python', args=['-c', 'import json,glob; files=glob.glob(\'monitoring/grafana/dashboards/*.json\')\nfor f in files:\n    d=json.loads(open(f).read())\n    assert len(d[\'panels\'])>=3, f\'{f}: only {len(d["panels"])} panels\'\nprint(\'PASS\')'], timeout=120)
        assert result.returncode == 0, (
            f'test_panels_count_minimum failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_panel_type_valid(self):
        """Verify all panels have a known Grafana panel type"""
        result = self._run_cmd('python', args=['-c', 'import json,glob; valid_types={\'graph\',\'timeseries\',\'stat\',\'gauge\',\'table\',\'text\',\'row\',\'heatmap\',\'barchart\',\'bargauge\',\'piechart\',\'logs\'}; files=glob.glob(\'monitoring/grafana/dashboards/*.json\')\nfor f in files:\n    d=json.loads(open(f).read())\n    for p in d[\'panels\']:\n        assert p.get(\'type\') in valid_types, f"{f}: unknown type \'{p.get(\'type\')}\'"\nprint(\'PASS\')'], timeout=120)
        assert result.returncode == 0, (
            f'test_panel_type_valid failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_provisioning_yaml_valid(self):
        """Verify provisioning YAML parses and has providers key"""
        result = self._run_cmd('python', args=['-c', "import yaml; prov=yaml.safe_load(open('monitoring/grafana/provisioning/dashboards.yml')); assert 'providers' in prov or 'apiVersion' in prov; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_provisioning_yaml_valid failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_uid_nonempty_string(self):
        """Verify uid is a non-empty string in all dashboards"""
        result = self._run_cmd('python', args=['-c', "import json,glob; files=glob.glob('monitoring/grafana/dashboards/*.json')\nfor f in files:\n    d=json.loads(open(f).read())\n    uid=d.get('uid','')\n    assert isinstance(uid,str) and len(uid)>0, f'{f}: uid is empty or not string'\nprint('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_uid_nonempty_string failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

