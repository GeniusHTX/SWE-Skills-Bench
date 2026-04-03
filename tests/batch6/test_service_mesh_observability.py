"""
Tests for 'service-mesh-observability' skill.
Generated from benchmark case definitions for service-mesh-observability.
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


class TestServiceMeshObservability:
    """Verify the service-mesh-observability skill output."""

    REPO_DIR = '/workspace/linkerd2'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestServiceMeshObservability.REPO_DIR, rel)

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

    def test_prometheus_config_exists(self):
        """Verify Prometheus config YAML exists"""
        _p = self._repo_path('observability/prometheus/config.yaml')
        assert os.path.isfile(_p), f'Missing file: observability/prometheus/config.yaml'
        self._load_yaml(_p)  # parse check

    def test_grafana_dashboards_dir_exists(self):
        """Verify Grafana dashboards directory with JSON files exists"""
        _p = self._repo_path('observability/grafana/dashboards/')
        assert os.path.isdir(_p), f'Missing directory: observability/grafana/dashboards/'

    def test_alerting_rules_exist(self):
        """Verify alerting rules YAML exists"""
        _p = self._repo_path('observability/prometheus/alerting-rules.yaml')
        assert os.path.isfile(_p), f'Missing file: observability/prometheus/alerting-rules.yaml'
        self._load_yaml(_p)  # parse check

    # ── semantic_check (static) ────────────────────────────────────────

    def test_prometheus_scrape_configs_structure(self):
        """Verify config.yaml has global section and scrape_configs with Istio jobs"""
        _p = self._repo_path('observability/prometheus/config.yaml')
        assert os.path.exists(_p), f'Missing: observability/prometheus/config.yaml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'global' in _all, 'Missing: global'
        assert 'scrape_configs' in _all, 'Missing: scrape_configs'
        assert 'job_name' in _all, 'Missing: job_name'
        assert 'istio' in _all, 'Missing: istio'
        assert 'envoy' in _all, 'Missing: envoy'

    def test_grafana_dashboard_panels_structure(self):
        """Verify Grafana dashboard JSON has panels with PromQL targets"""
        _p = self._repo_path('observability/grafana/dashboards/*.json')
        assert os.path.exists(_p), f'Missing: observability/grafana/dashboards/*.json'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'panels' in _all, 'Missing: panels'
        assert 'targets' in _all, 'Missing: targets'
        assert 'expr' in _all, 'Missing: expr'
        assert 'istio_request' in _all, 'Missing: istio_request'

    def test_alerting_rules_have_for_duration(self):
        """Verify alerting rules include 'for' duration to prevent flapping"""
        _p = self._repo_path('observability/prometheus/alerting-rules.yaml')
        assert os.path.exists(_p), f'Missing: observability/prometheus/alerting-rules.yaml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'groups' in _all, 'Missing: groups'
        assert 'rules' in _all, 'Missing: rules'
        assert 'alert' in _all, 'Missing: alert'
        assert 'expr' in _all, 'Missing: expr'
        assert 'for' in _all, 'Missing: for'

    # ── functional_check ────────────────────────────────────────

    def test_prometheus_yaml_valid(self):
        """Verify Prometheus config is valid YAML with scrape_configs"""
        self._ensure_setup('test_prometheus_yaml_valid', ['pip install pyyaml'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import yaml; c=yaml.safe_load(open('observability/prometheus/config.yaml')); assert 'scrape_configs' in c; assert len(c['scrape_configs'])>0; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_prometheus_yaml_valid failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_scrape_jobs_have_job_name(self):
        """Verify every scrape job has job_name key"""
        self._ensure_setup('test_scrape_jobs_have_job_name', ['pip install pyyaml'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import yaml; c=yaml.safe_load(open('observability/prometheus/config.yaml')); assert all('job_name' in j for j in c['scrape_configs']); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_scrape_jobs_have_job_name failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_grafana_dashboards_valid_json(self):
        """Verify all Grafana dashboard files are valid JSON"""
        result = self._run_cmd('python', args=['-c', "import json, pathlib; files=list(pathlib.Path('observability/grafana/dashboards').glob('*.json')); assert len(files)>0; [json.load(open(f)) for f in files]; print(f'PASS: {len(files)} dashboards valid')"], timeout=120)
        assert result.returncode == 0, (
            f'test_grafana_dashboards_valid_json failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_dashboard_panels_non_empty(self):
        """Verify dashboards have non-empty panels array"""
        result = self._run_cmd('python', args=['-c', "import json, pathlib; files=list(pathlib.Path('observability/grafana/dashboards').glob('*.json')); dashboards=[json.load(open(f)) for f in files]; assert all('panels' in d and len(d['panels'])>0 for d in dashboards); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_dashboard_panels_non_empty failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_alerting_rules_yaml_valid(self):
        """Verify alerting rules YAML is valid"""
        self._ensure_setup('test_alerting_rules_yaml_valid', ['pip install pyyaml'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import yaml; r=yaml.safe_load(open('observability/prometheus/alerting-rules.yaml')); assert 'groups' in r; assert len(r['groups'])>0; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_alerting_rules_yaml_valid failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_invalid_yaml_detected(self):
        """Verify invalid YAML syntax would be detected"""
        self._ensure_setup('test_invalid_yaml_detected', ['pip install pyyaml'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import yaml\ntry:\n    yaml.safe_load('{{invalid: yaml')\n    assert False\nexcept yaml.YAMLError:\n    print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_invalid_yaml_detected failed (exit {result.returncode})\n' + result.stderr[:500]
        )

