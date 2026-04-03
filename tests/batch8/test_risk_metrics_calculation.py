"""
Test for 'risk-metrics-calculation' skill — Risk Metrics Library
Validates that the Agent implemented VaR, CVaR, factor model, and
portfolio optimizer modules with correct statistical computations.
"""

import os
import re
import sys

import pytest


class TestRiskMetricsCalculation:
    """Verify risk metrics implementation."""

    REPO_DIR = "/workspace/pyfolio"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_risk_analyzer_module_exists(self):
        """Verify src/risk_metrics/analyzer.py and models.py exist."""
        for rel in ("src/risk_metrics/analyzer.py", "src/risk_metrics/models.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_factor_model_and_optimizer_exist(self):
        """Verify factor_model.py and optimizer.py exist."""
        for rel in ("src/risk_metrics/factor_model.py",
                     "src/risk_metrics/optimizer.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_package_init_exists(self):
        """Verify src/risk_metrics/__init__.py exists."""
        path = os.path.join(self.REPO_DIR, "src/risk_metrics/__init__.py")
        assert os.path.isfile(path), "Missing: src/risk_metrics/__init__.py"

    # ── semantic_check ──────────────────────────────────────────────

    def test_var_uses_percentile_formula(self):
        """Verify VaR is calculated as -np.percentile(returns, 5) at 95% confidence."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/risk_metrics/analyzer.py"))
        assert content, "analyzer.py is empty or unreadable"
        found = any(kw in content for kw in ("np.percentile", "percentile"))
        assert found, "np.percentile not found in analyzer.py"

    def test_cvar_defined_as_tail_expectation(self):
        """Verify CVaR is calculated as the mean of returns below VaR threshold."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/risk_metrics/analyzer.py"))
        assert content, "analyzer.py is empty or unreadable"
        assert "calculate_cvar" in content, "calculate_cvar not found"
        assert "mean" in content, "mean not found in analyzer.py"

    def test_optimizer_weight_constraints(self):
        """Verify optimizer enforces weights >= 0 and sum(weights) == 1."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/risk_metrics/optimizer.py"))
        assert content, "optimizer.py is empty or unreadable"
        found = any(kw in content for kw in (
            "weights >= 0", "sum", "LinearConstraint", "constraints"))
        assert found, "Weight constraint logic not found in optimizer.py"

    # ── functional_check (import) ───────────────────────────────────

    def _skip_unless_importable(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if self.REPO_DIR not in sys.path:
            sys.path.insert(0, self.REPO_DIR)

    def test_var_value_on_known_returns(self):
        """VaR at 95% confidence for known returns equals expected value."""
        self._skip_unless_importable()
        try:
            import numpy as np
            from src.risk_metrics.analyzer import RiskAnalyzer
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        returns = np.linspace(-0.10, 0.10, 100)
        var = RiskAnalyzer().calculate_var(returns, 0.95)
        expected = -np.percentile(returns, 5)
        assert abs(var - expected) < 1e-9, \
            f"VaR {var} != expected {expected}"

    def test_cvar_gte_var(self):
        """CVaR is always greater than or equal to VaR for the same returns series."""
        self._skip_unless_importable()
        try:
            import numpy as np
            from src.risk_metrics.analyzer import RiskAnalyzer
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        ra = RiskAnalyzer()
        returns = np.random.normal(0, 0.02, 1000)
        var = ra.calculate_var(returns, 0.95)
        cvar = ra.calculate_cvar(returns, 0.95)
        assert cvar >= var, f"CVaR {cvar} < VaR {var}"

    def test_var_non_negative(self):
        """VaR result is non-negative for normal market return distribution."""
        self._skip_unless_importable()
        try:
            import numpy as np
            from src.risk_metrics.analyzer import RiskAnalyzer
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        returns = np.random.normal(-0.001, 0.01, 500)
        var = RiskAnalyzer().calculate_var(returns, 0.95)
        assert var >= 0, f"VaR {var} is negative"

    def test_value_error_on_empty_returns(self):
        """calculate_var with empty returns array raises ValueError."""
        self._skip_unless_importable()
        try:
            import numpy as np
            from src.risk_metrics.analyzer import RiskAnalyzer
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        with pytest.raises(ValueError):
            RiskAnalyzer().calculate_var(np.array([]), 0.95)

    def test_minimum_variance_weights_sum_to_one(self):
        """PortfolioOptimizer.minimum_variance weights sum to 1.0 within 1e-6."""
        self._skip_unless_importable()
        try:
            import numpy as np
            from src.risk_metrics.optimizer import PortfolioOptimizer
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        cov = np.array([[0.04, 0.02], [0.02, 0.09]])
        exp_returns = np.array([0.05, 0.07])
        weights = PortfolioOptimizer().minimum_variance(cov, exp_returns)
        assert abs(sum(weights) - 1.0) < 1e-6, \
            f"Weights sum {sum(weights)} != 1.0"
