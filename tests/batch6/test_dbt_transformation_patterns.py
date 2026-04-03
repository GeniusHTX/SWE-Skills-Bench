"""
Tests for 'dbt-transformation-patterns' skill.
Generated from benchmark case definitions for dbt-transformation-patterns.
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


class TestDbtTransformationPatterns:
    """Verify the dbt-transformation-patterns skill output."""

    REPO_DIR = '/workspace/dbt-core'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestDbtTransformationPatterns.REPO_DIR, rel)

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

    def test_dbt_project_yml_exists(self):
        """Verify dbt_project.yml exists at root"""
        _p = self._repo_path('dbt_project.yml')
        assert os.path.isfile(_p), f'Missing file: dbt_project.yml'
        self._load_yaml(_p)  # parse check

    def test_staging_models_exist(self):
        """Verify staging SQL models exist"""
        _p = self._repo_path('models/staging/stg_orders.sql')
        assert os.path.isfile(_p), f'Missing file: models/staging/stg_orders.sql'
        _p = self._repo_path('models/staging/stg_customers.sql')
        assert os.path.isfile(_p), f'Missing file: models/staging/stg_customers.sql'

    def test_mart_model_exists(self):
        """Verify mart sales summary model exists"""
        _p = self._repo_path('models/marts/mart_sales_summary.sql')
        assert os.path.isfile(_p), f'Missing file: models/marts/mart_sales_summary.sql'

    # ── semantic_check (static) ────────────────────────────────────────

    def test_staging_uses_source_macro(self):
        """Verify staging models use {{ source() }} macro (not hardcoded tables)"""
        _p = self._repo_path('models/staging/stg_orders.sql')
        assert os.path.exists(_p), f'Missing: models/staging/stg_orders.sql'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert re.search('{{ source(', _all, re.MULTILINE), 'Pattern not found: {{ source('

    def test_mart_uses_ref_macro(self):
        """Verify mart model uses {{ ref() }} to reference upstream models"""
        _p = self._repo_path('models/marts/mart_sales_summary.sql')
        assert os.path.exists(_p), f'Missing: models/marts/mart_sales_summary.sql'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert re.search('{{ ref(', _all, re.MULTILINE), 'Pattern not found: {{ ref('
        assert 'GROUP BY' in _all, 'Missing: GROUP BY'

    def test_schema_yml_tests_defined(self):
        """Verify schema.yml has not_null and unique column tests"""
        _p = self._repo_path('models/staging/schema.yml')
        assert os.path.exists(_p), f'Missing: models/staging/schema.yml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'not_null' in _all, 'Missing: not_null'
        assert 'unique' in _all, 'Missing: unique'
        assert 'tests' in _all, 'Missing: tests'

    def test_cte_pattern_in_staging(self):
        """Verify staging models follow CTE pattern (WITH ... AS)"""
        _p = self._repo_path('models/staging/stg_orders.sql')
        assert os.path.exists(_p), f'Missing: models/staging/stg_orders.sql'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'WITH' in _all, 'Missing: WITH'
        assert re.search('AS (', _all, re.MULTILINE), 'Pattern not found: AS ('

    # ── functional_check ────────────────────────────────────────

    def test_dbt_project_yml_valid_yaml(self):
        """Verify dbt_project.yml is valid parseable YAML"""
        result = self._run_cmd('python', args=['-c', "import yaml; proj=yaml.safe_load(open('dbt_project.yml')); assert 'models' in proj and 'name' in proj; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_dbt_project_yml_valid_yaml failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_mart_materialization_table(self):
        """Verify mart models materialized as 'table' in dbt_project.yml"""
        result = self._run_cmd('python', args=['-c', "import yaml; p=yaml.safe_load(open('dbt_project.yml')); m=str(p.get('models',{})); assert 'table' in m, 'No table materialization found'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_mart_materialization_table failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_staging_source_not_hardcoded(self):
        """Verify staging models do NOT use hardcoded table names"""
        result = self._run_cmd('python', args=['-c', "sql=open('models/staging/stg_orders.sql').read(); assert '{{ source(' in sql, 'Missing source() macro in staging'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_staging_source_not_hardcoded failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_mart_has_group_by(self):
        """Verify mart SQL contains GROUP BY and aggregate functions"""
        result = self._run_cmd('python', args=['-c', "sql=open('models/marts/mart_sales_summary.sql').read().upper(); assert 'GROUP BY' in sql and ('SUM' in sql or 'COUNT' in sql or 'AVG' in sql); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_mart_has_group_by failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_freshness_thresholds_in_sources(self):
        """Verify source freshness thresholds are configured"""
        result = self._run_cmd('python', args=['-c', "import yaml,glob; files=glob.glob('models/**/sources.yml',recursive=True)+glob.glob('models/**/schema.yml',recursive=True); found=False;\nfor f in files:\n    d=yaml.safe_load(open(f))\n    if d and 'sources' in str(d) and 'freshness' in str(d): found=True; break\nassert found, 'No freshness config found'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_freshness_thresholds_in_sources failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

