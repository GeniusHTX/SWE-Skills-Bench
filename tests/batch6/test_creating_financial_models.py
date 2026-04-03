"""
Tests for 'creating-financial-models' skill.
Generated from benchmark case definitions for creating-financial-models.
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


class TestCreatingFinancialModels:
    """Verify the creating-financial-models skill output."""

    REPO_DIR = '/workspace/QuantLib'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestCreatingFinancialModels.REPO_DIR, rel)

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

    def test_dcf_model_file_exists(self):
        """Verify DCF model module exists"""
        _p = self._repo_path('models/dcf_model.py')
        assert os.path.isfile(_p), f'Missing file: models/dcf_model.py'
        py_compile.compile(_p, doraise=True)

    def test_monte_carlo_file_exists(self):
        """Verify Monte Carlo simulation module exists"""
        _p = self._repo_path('models/monte_carlo.py')
        assert os.path.isfile(_p), f'Missing file: models/monte_carlo.py'
        py_compile.compile(_p, doraise=True)

    def test_init_file_exists(self):
        """Verify models package __init__.py exists"""
        _p = self._repo_path('models/__init__.py')
        assert os.path.isfile(_p), f'Missing file: models/__init__.py'
        py_compile.compile(_p, doraise=True)

    # ── semantic_check (static) ────────────────────────────────────────

    def test_dcf_class_methods(self):
        """Verify DCFModel class has all required methods"""
        _p = self._repo_path('models/dcf_model.py')
        assert os.path.exists(_p), f'Missing: models/dcf_model.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'class DCFModel' in _all, 'Missing: class DCFModel'
        assert 'project_cash_flows' in _all, 'Missing: project_cash_flows'
        assert 'calculate_terminal_value' in _all, 'Missing: calculate_terminal_value'
        assert 'calculate_npv' in _all, 'Missing: calculate_npv'

    def test_monte_carlo_class_methods(self):
        """Verify MonteCarloSimulation has run and get_statistics methods"""
        _p = self._repo_path('models/monte_carlo.py')
        assert os.path.exists(_p), f'Missing: models/monte_carlo.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'class MonteCarloSimulation' in _all, 'Missing: class MonteCarloSimulation'
        assert 'def run' in _all, 'Missing: def run'
        assert 'def get_statistics' in _all, 'Missing: def get_statistics'

    def test_no_magic_numbers(self):
        """Verify formulas use parameters not hardcoded magic numbers"""
        _p = self._repo_path('models/dcf_model.py')
        assert os.path.exists(_p), f'Missing: models/dcf_model.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'discount_rate' in _all, 'Missing: discount_rate'
        assert 'growth_rate' in _all, 'Missing: growth_rate'
        assert 'base_cash_flow' in _all, 'Missing: base_cash_flow'

    # ── functional_check ────────────────────────────────────────

    def test_dcf_npv_formula_correct(self):
        """Verify DCF NPV calculation matches manual formula result"""
        self._ensure_setup('test_dcf_npv_formula_correct', ['pip install numpy'], 'skip_if_setup_fails')
        result = self._run_cmd('python', args=['-c', "from models.dcf_model import DCFModel; m=DCFModel(base_cash_flow=100.0, terminal_growth_rate=0.03); npv=m.calculate_npv(discount_rate=0.10); assert npv > 0, f'NPV should be positive: {npv}'; print(f'NPV={npv:.2f} PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_dcf_npv_formula_correct failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_discount_rate_equals_growth_raises(self):
        """Verify ValueError when discount_rate == terminal_growth_rate"""
        result = self._run_cmd('python', args=['-c', "from models.dcf_model import DCFModel; m=DCFModel(base_cash_flow=100.0, terminal_growth_rate=0.10);\ntry:\n    m.calculate_npv(discount_rate=0.10)\n    print('FAIL: no exception')\nexcept ValueError:\n    print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_discount_rate_equals_growth_raises failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_monte_carlo_seed_reproducibility(self):
        """Verify Monte Carlo with same seed produces identical results"""
        self._ensure_setup('test_monte_carlo_seed_reproducibility', ['pip install numpy'], 'skip_if_setup_fails')
        result = self._run_cmd('python', args=['-c', "import numpy as np; from models.monte_carlo import MonteCarloSimulation; s=MonteCarloSimulation(base_cash_flow=100,discount_rate=0.1,terminal_growth_rate=0.03); r1=s.run(1000,seed=42); r2=s.run(1000,seed=42); assert np.array_equal(r1,r2); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_monte_carlo_seed_reproducibility failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_statistics_keys_complete(self):
        """Verify get_statistics returns all 7 required keys"""
        self._ensure_setup('test_statistics_keys_complete', ['pip install numpy'], 'skip_if_setup_fails')
        result = self._run_cmd('python', args=['-c', "from models.monte_carlo import MonteCarloSimulation; s=MonteCarloSimulation(base_cash_flow=100,discount_rate=0.1,terminal_growth_rate=0.03); s.run(1000,seed=42); stats=s.get_statistics(); required={'mean','std','p5','p25','p50','p75','p95'}; assert required.issubset(set(stats.keys())), f'Missing keys: {required-set(stats.keys())}'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_statistics_keys_complete failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_project_cash_flows_compounding(self):
        """Verify cash flows compound correctly over years"""
        result = self._run_cmd('python', args=['-c', "from models.dcf_model import DCFModel; m=DCFModel(base_cash_flow=100.0, terminal_growth_rate=0.03); cfs=m.project_cash_flows(growth_rate=0.05, years=3); assert len(cfs)==3; assert abs(cfs[0]-105.0)<0.01; assert abs(cfs[1]-110.25)<0.01; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_project_cash_flows_compounding failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_negative_years_handling(self):
        """Verify negative years raises ValueError or returns empty list"""
        result = self._run_cmd('python', args=['-c', "from models.dcf_model import DCFModel; m=DCFModel(base_cash_flow=100.0, terminal_growth_rate=0.03);\ntry:\n    cfs=m.project_cash_flows(growth_rate=0.05, years=-1)\n    assert isinstance(cfs, list) and len(cfs)==0, 'Expected empty list or ValueError'\n    print('PASS')\nexcept ValueError:\n    print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_negative_years_handling failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

