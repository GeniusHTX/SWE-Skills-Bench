"""
Tests for 'risk-metrics-calculation' skill.
Generated from benchmark case definitions for risk-metrics-calculation.
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


class TestRiskMetricsCalculation:
    """Verify the risk-metrics-calculation skill output."""

    REPO_DIR = '/workspace/pyfolio'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestRiskMetricsCalculation.REPO_DIR, rel)

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

    def test_risk_modules_exist(self):
        """Verify all risk analysis modules exist"""
        _p = self._repo_path('risk/metrics.py')
        assert os.path.isfile(_p), f'Missing file: risk/metrics.py'
        py_compile.compile(_p, doraise=True)
        _p = self._repo_path('risk/portfolio.py')
        assert os.path.isfile(_p), f'Missing file: risk/portfolio.py'
        py_compile.compile(_p, doraise=True)
        _p = self._repo_path('risk/drawdown.py')
        assert os.path.isfile(_p), f'Missing file: risk/drawdown.py'
        py_compile.compile(_p, doraise=True)
        _p = self._repo_path('risk/ratios.py')
        assert os.path.isfile(_p), f'Missing file: risk/ratios.py'
        py_compile.compile(_p, doraise=True)

    def test_risk_test_file_exists(self):
        """Verify test file exists"""
        _p = self._repo_path('tests/test_risk_metrics.py')
        assert os.path.isfile(_p), f'Missing file: tests/test_risk_metrics.py'
        py_compile.compile(_p, doraise=True)

    # ── semantic_check (static) ────────────────────────────────────────

    def test_risk_metrics_class_shape(self):
        """Verify RiskMetrics class with VaR/CVaR methods"""
        _p = self._repo_path('risk/metrics.py')
        assert os.path.exists(_p), f'Missing: risk/metrics.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'class RiskMetrics' in _all, 'Missing: class RiskMetrics'
        assert 'var_historical' in _all, 'Missing: var_historical'
        assert 'var_parametric' in _all, 'Missing: var_parametric'
        assert 'var_cornish_fisher' in _all, 'Missing: var_cornish_fisher'
        assert 'cvar' in _all, 'Missing: cvar'
        assert 'var_n_day' in _all, 'Missing: var_n_day'

    def test_portfolio_risk_component_var(self):
        """Verify PortfolioRisk has component_var returning DataFrame"""
        _p = self._repo_path('risk/portfolio.py')
        assert os.path.exists(_p), f'Missing: risk/portfolio.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'class PortfolioRisk' in _all, 'Missing: class PortfolioRisk'
        assert 'component_var' in _all, 'Missing: component_var'
        assert 'marginal_var' in _all, 'Missing: marginal_var'
        assert 'pct_contribution' in _all, 'Missing: pct_contribution'
        assert 'portfolio_volatility' in _all, 'Missing: portfolio_volatility'

    def test_drawdown_analyzer_class(self):
        """Verify DrawdownAnalyzer with max_drawdown method"""
        _p = self._repo_path('risk/drawdown.py')
        assert os.path.exists(_p), f'Missing: risk/drawdown.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'class DrawdownAnalyzer' in _all, 'Missing: class DrawdownAnalyzer'
        assert 'max_drawdown' in _all, 'Missing: max_drawdown'
        assert 'drawdown_periods' in _all, 'Missing: drawdown_periods'

    def test_ratio_functions(self):
        """Verify ratio calculation functions defined"""
        _p = self._repo_path('risk/ratios.py')
        assert os.path.exists(_p), f'Missing: risk/ratios.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'sharpe_ratio' in _all, 'Missing: sharpe_ratio'
        assert 'sortino_ratio' in _all, 'Missing: sortino_ratio'
        assert 'calmar_ratio' in _all, 'Missing: calmar_ratio'
        assert 'omega_ratio' in _all, 'Missing: omega_ratio'

    # ── functional_check ────────────────────────────────────────

    def test_var_historical_known_value(self):
        """Verify var_historical returns negative of 5th percentile"""
        self._ensure_setup('test_var_historical_known_value', ['pip install pandas numpy scipy'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import pandas as pd, numpy as np; returns=pd.Series(np.random.normal(0.001,0.02,1000)); from risk.metrics import RiskMetrics; rm=RiskMetrics(returns); var=rm.var_historical(0.95); expected=-np.percentile(returns,5); assert abs(var-expected)<1e-10; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_var_historical_known_value failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_cvar_gte_var_invariant(self):
        """Verify CVaR >= VaR at same confidence level"""
        self._ensure_setup('test_cvar_gte_var_invariant', ['pip install pandas numpy scipy'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import pandas as pd, numpy as np; returns=pd.Series(np.random.normal(0.001,0.02,1000)); from risk.metrics import RiskMetrics; rm=RiskMetrics(returns); var=rm.var_historical(0.95); cvar=rm.cvar(0.95); assert cvar>=var; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_cvar_gte_var_invariant failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_component_var_sums_to_total(self):
        """Verify component VaR sums to total portfolio VaR"""
        self._ensure_setup('test_component_var_sums_to_total', ['pip install pandas numpy scipy'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_risk_metrics.py', '-v', '-k', 'test_component_var_sum'], timeout=120)
        assert result.returncode == 0, (
            f'test_component_var_sums_to_total failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_monotonic_series_zero_drawdown(self):
        """Verify monotonically increasing series has max_drawdown = 0"""
        self._ensure_setup('test_monotonic_series_zero_drawdown', ['pip install pandas numpy'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import pandas as pd, numpy as np; prices=pd.Series(np.cumsum(np.ones(100))); from risk.drawdown import DrawdownAnalyzer; da=DrawdownAnalyzer(prices); assert da.max_drawdown()==0.0; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_monotonic_series_zero_drawdown failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_weights_not_summing_to_one(self):
        """Verify PortfolioRisk rejects weights not summing to 1.0"""
        self._ensure_setup('test_weights_not_summing_to_one', ['pip install pandas numpy'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import pandas as pd, numpy as np; returns=pd.DataFrame(np.random.normal(0,0.01,(100,2))); from risk.portfolio import PortfolioRisk\ntry:\n    PortfolioRisk(returns, np.array([0.3, 0.3]))\n    assert False, 'Should have raised'\nexcept ValueError:\n    print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_weights_not_summing_to_one failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_full_risk_suite(self):
        """Run the full risk metrics test suite"""
        self._ensure_setup('test_full_risk_suite', ['pip install pandas numpy scipy pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_risk_metrics.py', '-v', '--tb=short'], timeout=120)
        assert result.returncode == 0, (
            f'test_full_risk_suite failed (exit {result.returncode})\n' + result.stderr[:500]
        )

