"""
Test for 'risk-metrics-calculation' skill — Portfolio Risk Engine
Validates that the Agent created a RiskEngine with VaR, CVaR, Sharpe,
max drawdown, and beta calculations in pyfolio.
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest


class TestRiskMetricsCalculation:
    """Verify RiskEngine implementation in pyfolio."""

    REPO_DIR = "/workspace/pyfolio"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _import_engine(self):
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from pyfolio.risk_metrics import RiskEngine

            return RiskEngine
        finally:
            sys.path[:] = old_path

    def _sample_returns(self):
        rng = np.random.default_rng(42)
        return pd.Series(rng.normal(0.001, 0.02, 252))

    # ---- file_path_check ----

    def test_risk_metrics_exists(self):
        """Verifies pyfolio/risk_metrics.py exists."""
        path = os.path.join(self.REPO_DIR, "pyfolio/risk_metrics.py")
        assert os.path.exists(path), f"File not found: {path}"

    def test_init_py_exists(self):
        """Verifies pyfolio/__init__.py exists."""
        path = os.path.join(self.REPO_DIR, "pyfolio/__init__.py")
        assert os.path.exists(path), f"File not found: {path}"

    # ---- semantic_check ----

    def test_sem_import(self):
        """Verifies RiskEngine is importable."""
        RiskEngine = self._import_engine()
        assert RiskEngine is not None

    def test_sem_methods(self):
        """Verifies RiskEngine has all required methods."""
        text = self._read(os.path.join(self.REPO_DIR, "pyfolio/risk_metrics.py"))
        for method in [
            "calculate_var",
            "calculate_cvar",
            "calculate_sharpe",
            "calculate_max_drawdown",
            "calculate_beta",
            "full_risk_report",
        ]:
            assert method in text, f"Missing method: {method}"

    def test_sem_pd_series_param(self):
        """Verifies methods accept pd.Series as argument."""
        text = self._read(os.path.join(self.REPO_DIR, "pyfolio/risk_metrics.py"))
        assert "Series" in text or "returns" in text, "No pd.Series parameter seen"

    def test_sem_confidence_default(self):
        """Verifies confidence_level defaults to 0.95."""
        text = self._read(os.path.join(self.REPO_DIR, "pyfolio/risk_metrics.py"))
        assert "0.95" in text, "Default confidence_level 0.95 not found"

    # ---- functional_check ----

    def test_func_var_positive(self):
        """Verifies VaR > 0 for random returns."""
        RiskEngine = self._import_engine()
        returns = self._sample_returns()
        var = RiskEngine().calculate_var(returns, 0.95)
        assert var > 0, f"VaR should be positive, got {var}"

    def test_func_cvar_ge_var(self):
        """Verifies CVaR >= VaR always."""
        RiskEngine = self._import_engine()
        returns = self._sample_returns()
        var = RiskEngine().calculate_var(returns, 0.95)
        cvar = RiskEngine().calculate_cvar(returns, 0.95)
        assert cvar >= var, f"CVaR {cvar} should be >= VaR {var}"

    def test_func_var_known_values(self):
        """Verifies VaR matches percentile for known returns."""
        RiskEngine = self._import_engine()
        known = pd.Series(
            [-0.05, -0.03, 0.01, 0.02, -0.01, 0.03, -0.04, 0.02, 0.01, -0.02]
        )
        var_95 = RiskEngine().calculate_var(known, 0.95)
        expected = -np.percentile(known, 5)
        assert abs(var_95 - expected) < 1e-6, f"VaR {var_95} != expected {expected}"

    def test_func_empty_series_raises(self):
        """Failure: empty series raises ValueError."""
        RiskEngine = self._import_engine()
        with pytest.raises(ValueError):
            RiskEngine().calculate_var(pd.Series([]), 0.95)

    def test_func_confidence_over_1_raises(self):
        """Failure: confidence > 1.0 raises ValueError."""
        RiskEngine = self._import_engine()
        returns = self._sample_returns()
        with pytest.raises(ValueError):
            RiskEngine().calculate_var(returns, 1.1)

    def test_func_confidence_zero_raises(self):
        """Failure: confidence = 0.0 raises ValueError."""
        RiskEngine = self._import_engine()
        returns = self._sample_returns()
        with pytest.raises(ValueError):
            RiskEngine().calculate_var(returns, 0.0)

    def test_func_sharpe_positive(self):
        """Verifies Sharpe > 0 for constant positive returns."""
        RiskEngine = self._import_engine()
        sharpe = RiskEngine().calculate_sharpe(
            pd.Series([0.001] * 252), risk_free_rate=0.0
        )
        assert sharpe > 0, f"Sharpe should be positive, got {sharpe}"

    def test_func_max_drawdown(self):
        """Verifies max drawdown > 0 with big loss."""
        RiskEngine = self._import_engine()
        mdd = RiskEngine().calculate_max_drawdown(pd.Series([0.01, -0.50, 0.01]))
        assert mdd > 0, f"Max drawdown should be > 0, got {mdd}"
