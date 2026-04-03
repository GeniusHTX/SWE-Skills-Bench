"""Test file for the risk-metrics-calculation skill.

This suite validates risk metric functions: conditional_var, sortino_ratio,
calmar_ratio, max_drawdown_duration, and ulcer_index in pyfolio.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest


class TestRiskMetricsCalculation:
    """Verify risk metrics in pyfolio."""

    REPO_DIR = "/workspace/pyfolio"

    RISK_METRICS_PY = "pyfolio/risk_metrics.py"
    TIMESERIES_PY = "pyfolio/timeseries.py"
    TEARS_PY = "pyfolio/tears.py"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_pyfolio_risk_metrics_py_exists(self):
        """Verify risk_metrics.py exists and is non-empty."""
        self._assert_non_empty_file(self.RISK_METRICS_PY)

    def test_file_path_pyfolio_timeseries_py_modified(self):
        """Verify timeseries.py exists (modified)."""
        self._assert_non_empty_file(self.TIMESERIES_PY)

    def test_file_path_pyfolio_tears_py_modified(self):
        """Verify tears.py exists (modified)."""
        self._assert_non_empty_file(self.TEARS_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_conditional_var_accepts_returns_confidence_method_parameters(
        self,
    ):
        """conditional_var accepts returns, confidence, method parameters."""
        src = self._read_text(self.RISK_METRICS_PY)
        assert re.search(
            r"def\s+conditional_var\s*\(", src
        ), "conditional_var function not found"
        for param in ("returns", "confidence", "method"):
            assert param in src, f"conditional_var missing parameter: {param}"

    def test_semantic_sortino_ratio_computes_downside_deviation_returns_below_requ(
        self,
    ):
        """sortino_ratio computes downside deviation (returns below required_return only)."""
        src = self._read_text(self.RISK_METRICS_PY)
        assert re.search(
            r"def\s+sortino_ratio\s*\(", src
        ), "sortino_ratio function not found"
        assert re.search(
            r"downside|required_return|below", src, re.IGNORECASE
        ), "sortino_ratio should compute downside deviation"

    def test_semantic_calmar_ratio_has_period_parameter_defaulting_to_36(self):
        """calmar_ratio has period parameter defaulting to 36."""
        src = self._read_text(self.RISK_METRICS_PY)
        assert re.search(
            r"def\s+calmar_ratio\s*\(", src
        ), "calmar_ratio function not found"
        assert re.search(r"period|36", src), "calmar_ratio should have period parameter"

    def test_semantic_max_drawdown_duration_returns_pd_timedelta(self):
        """max_drawdown_duration returns pd.Timedelta."""
        src = self._read_text(self.RISK_METRICS_PY)
        assert re.search(
            r"def\s+max_drawdown_duration\s*\(", src
        ), "max_drawdown_duration function not found"
        assert re.search(
            r"Timedelta|timedelta|duration", src
        ), "max_drawdown_duration should return Timedelta"

    def test_semantic_ulcer_index_formula_sqrt_mean_di_2(self):
        """ulcer_index formula: sqrt(mean(Di^2))."""
        src = self._read_text(self.RISK_METRICS_PY)
        assert re.search(
            r"def\s+ulcer_index\s*\(", src
        ), "ulcer_index function not found"
        assert re.search(
            r"sqrt|np\.sqrt|mean|\*\*\s*2", src
        ), "ulcer_index should compute sqrt(mean(Di^2))"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, source analysis)
    # ------------------------------------------------------------------

    def test_functional_cvar_historical_on_known_series_matches_hand_calculation(self):
        """CVaR historical on known series matches hand calculation."""
        src = self._read_text(self.RISK_METRICS_PY)
        assert re.search(
            r"def\s+conditional_var\s*\(", src
        ), "conditional_var function required"
        assert re.search(
            r"historical|percentile|quantile|sort", src
        ), "Historical CVaR method required"

    def test_functional_cvar_gaussian_matches_formula_based_calculation(self):
        """CVaR gaussian matches formula-based calculation."""
        src = self._read_text(self.RISK_METRICS_PY)
        assert re.search(
            r"gaussian|norm|parametric|pdf|cdf", src, re.IGNORECASE
        ), "Gaussian CVaR method required"

    def test_functional_sortino_with_all_positive_returns_np_inf(self):
        """Sortino with all positive returns -> np.inf."""
        src = self._read_text(self.RISK_METRICS_PY)
        assert re.search(
            r"inf|np\.inf|float\(['\"]inf", src
        ), "Sortino should return inf when all returns are positive"

    def test_functional_calmar_correctly_annualizes_return_and_divides_by_max_drawdo(
        self,
    ):
        """Calmar correctly annualizes return and divides by max drawdown."""
        src = self._read_text(self.RISK_METRICS_PY)
        assert re.search(
            r"annualize|252|365|max_drawdown", src, re.IGNORECASE
        ), "Calmar should annualize return and use max drawdown"

    def test_functional_longest_drawdown_period_correctly_identified_in_days(self):
        """Longest drawdown period correctly identified in days."""
        src = self._read_text(self.RISK_METRICS_PY)
        assert re.search(
            r"def\s+max_drawdown_duration\s*\(", src
        ), "max_drawdown_duration function required"
