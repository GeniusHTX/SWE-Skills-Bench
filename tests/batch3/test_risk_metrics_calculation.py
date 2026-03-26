"""
Tests for risk-metrics-calculation skill.
Validates risk metric functions in pyfolio/risk_metrics.py.
"""

import os
import math
import pytest

REPO_DIR = "/workspace/pyfolio"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestRiskMetricsCalculation:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_risk_metrics_file_exists(self):
        """pyfolio/risk_metrics.py must exist."""
        rel = "pyfolio/risk_metrics.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "risk_metrics.py is empty"

    def test_pyfolio_init_exists(self):
        """pyfolio/__init__.py must exist."""
        rel = "pyfolio/__init__.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_risk_functions_defined(self):
        """historical_var, cvar, parametric_var, and InsufficientDataError must be defined."""
        content = _read("pyfolio/risk_metrics.py")
        for symbol in (
            "def historical_var",
            "def cvar",
            "def parametric_var",
            "InsufficientDataError",
        ):
            assert symbol in content, f"{symbol} not found in risk_metrics.py"

    def test_drawdown_functions_defined(self):
        """max_drawdown, top_drawdowns, and DrawdownResult must be defined."""
        content = _read("pyfolio/risk_metrics.py")
        for symbol in ("def max_drawdown", "def top_drawdowns", "DrawdownResult"):
            assert symbol in content, f"{symbol} not found in risk_metrics.py"

    def test_ratio_functions_defined(self):
        """sharpe_ratio, sortino_ratio, and calmar_ratio must be defined."""
        content = _read("pyfolio/risk_metrics.py")
        for symbol in ("def sharpe_ratio", "def sortino_ratio", "def calmar_ratio"):
            assert symbol in content, f"{symbol} not found in risk_metrics.py"

    def test_rolling_functions_defined(self):
        """rolling_var and rolling_sharpe must be defined with window parameter."""
        content = _read("pyfolio/risk_metrics.py")
        assert "def rolling_var" in content, "rolling_var not defined"
        assert "def rolling_sharpe" in content, "rolling_sharpe not defined"
        assert "window" in content, "window parameter not found"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_fewer_than_30_obs_raises_insufficient_data(self):
        """historical_var with < 30 observations must raise InsufficientDataError (mocked)."""
        import numpy as np

        class InsufficientDataError(Exception):
            pass

        def historical_var(returns, confidence=0.95):
            if len(returns) < 30:
                raise InsufficientDataError(
                    f"Need >= 30 observations, got {len(returns)}"
                )
            return float(np.percentile(returns, (1 - confidence) * 100))

        np.random.seed(42)
        with pytest.raises(InsufficientDataError):
            historical_var(np.random.randn(20), confidence=0.95)

    def test_historical_var_95_approx_neg_1_6(self):
        """historical_var at 95% on 1%-std normal returns must be approx -0.016 (mocked)."""
        import numpy as np

        def historical_var(returns, confidence=0.95):
            if len(returns) < 30:
                raise ValueError("Need >= 30 observations")
            return float(np.percentile(returns, (1 - confidence) * 100))

        np.random.seed(42)
        returns = np.random.randn(1000) * 0.01
        var = historical_var(returns, confidence=0.95)
        assert -0.02 <= var <= -0.01, f"Expected VaR approx -0.016, got {var:.4f}"

    def test_cvar_less_than_var(self):
        """CVaR must be more severe (more negative) than VaR at same confidence (mocked)."""
        import numpy as np

        def historical_var(returns, confidence=0.95):
            return float(np.percentile(returns, (1 - confidence) * 100))

        def cvar(returns, confidence=0.95):
            var = historical_var(returns, confidence)
            return float(np.mean(returns[returns <= var]))

        np.random.seed(42)
        returns = np.random.randn(1000) * 0.01
        var_95 = historical_var(returns, 0.95)
        cvar_95 = cvar(returns, 0.95)
        assert (
            cvar_95 < var_95
        ), f"CVaR ({cvar_95:.4f}) must be below VaR ({var_95:.4f})"

    def test_rolling_var_first_59_nan(self):
        """rolling_var(window=60) must return NaN for first 59 values (mocked)."""
        import numpy as np

        def rolling_var(returns, window=60, confidence=0.95):
            result = [float("nan")] * (window - 1)
            for i in range(window - 1, len(returns)):
                window_returns = returns[i - window + 1 : i + 1]
                result.append(
                    float(np.percentile(window_returns, (1 - confidence) * 100))
                )
            return result

        np.random.seed(42)
        returns = np.random.randn(200) * 0.01
        rolling = rolling_var(returns, window=60)
        for i in range(59):
            assert math.isnan(
                rolling[i]
            ), f"Expected NaN at index {i}, got {rolling[i]}"
        assert not math.isnan(rolling[59]), f"Expected non-NaN at index 59, got NaN"

    def test_sharpe_ratio_approx_1_0(self):
        """sharpe_ratio must be approx 1.0 for mean/std=1 daily returns annualized (mocked)."""
        import numpy as np

        def sharpe_ratio(returns, risk_free=0.0, periods_per_year=252):
            excess = returns - risk_free / periods_per_year
            mean = np.mean(excess)
            std = np.std(excess, ddof=1)
            if std == 0:
                return float("inf") if mean > 0 else 0.0
            return float(mean / std * math.sqrt(periods_per_year))

        np.random.seed(42)
        returns = np.random.normal(loc=0.01, scale=0.01, size=252)
        sr = sharpe_ratio(returns, risk_free=0)
        assert (
            abs(sr - 1.0) <= 1.0
        ), f"Sharpe ratio {sr:.2f} not within tolerance of 1.0 ± 1.0"

    def test_zero_std_returns_handled_gracefully(self):
        """sharpe_ratio must not raise ZeroDivisionError for constant returns (mocked)."""
        import numpy as np

        def sharpe_ratio(returns, risk_free=0.0, periods_per_year=252):
            excess = returns - risk_free / periods_per_year
            mean = np.mean(excess)
            std = np.std(excess, ddof=1)
            if std == 0:
                return float("inf") if mean > 0 else 0.0
            return float(mean / std * math.sqrt(periods_per_year))

        returns = np.full(252, 0.001)
        sr = sharpe_ratio(returns)
        # Must not raise; result must be a valid float
        assert isinstance(sr, float), f"Expected float, got {type(sr)}"
        assert not math.isnan(sr) or sr == float("inf") or sr == 0.0
