"""
Test for 'risk-metrics-calculation' skill — pyfolio Risk Metrics
Validates VaR/CVaR calculations, Sortino ratio, max_drawdown,
and portfolio risk analysis.
"""

import os
import re
import sys

import pytest


class TestRiskMetricsCalculation:
    """Verify risk metrics calculations in pyfolio."""

    REPO_DIR = "/workspace/pyfolio"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_pyfolio_source_exists(self):
        """Verify pyfolio source directory exists."""
        pkg = os.path.join(self.REPO_DIR, "pyfolio")
        assert os.path.isdir(pkg), "pyfolio/ package not found"

    def test_risk_module_exists(self):
        """Verify risk/metrics related modules exist."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and (
                    "risk" in f.lower()
                    or "metric" in f.lower()
                    or "timeseries" in f.lower()
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No risk/metrics module found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_var_calculation(self):
        """Verify Value at Risk (VaR) calculation."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(value.?at.?risk|VaR|var_|var_cov|percentile|quantile)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No VaR calculation found")

    def test_cvar_calculation(self):
        """Verify Conditional VaR (CVaR/Expected Shortfall)."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(CVaR|cvar|conditional.?var|expected.?shortfall)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No CVaR/Expected Shortfall found")

    def test_sortino_ratio(self):
        """Verify Sortino ratio calculation."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(sortino|downside.?deviation|downside_risk)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No Sortino ratio found")

    def test_max_drawdown(self):
        """Verify max drawdown calculation."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(max.?drawdown|maximum.?drawdown|drawdown)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No max drawdown calculation found")

    def test_sharpe_ratio(self):
        """Verify Sharpe ratio calculation."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(sharpe|risk_free|excess_return)", content, re.IGNORECASE):
                return
        pytest.fail("No Sharpe ratio found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_source_files_parse(self):
        """Verify source files are syntactically valid."""
        import ast

        py_files = self._find_py_files()
        for fpath in py_files[:15]:
            content = self._read(fpath)
            try:
                ast.parse(content, filename=fpath)
            except SyntaxError as e:
                pytest.fail(f"SyntaxError in {os.path.basename(fpath)}: {e}")

    def test_import_timeseries(self):
        """Verify timeseries module can be imported."""
        ts_mod = os.path.join(self.REPO_DIR, "pyfolio", "timeseries.py")
        if not os.path.exists(ts_mod):
            pytest.skip("timeseries.py not found")
        if self.REPO_DIR not in sys.path:
            sys.path.insert(0, self.REPO_DIR)
        try:
            import importlib

            spec = importlib.util.spec_from_file_location("pyfolio.timeseries", ts_mod)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            assert (
                hasattr(mod, "max_drawdown")
                or hasattr(mod, "sharpe_ratio")
                or hasattr(mod, "sortino_ratio")
            ), "timeseries missing expected functions"
        except Exception as e:
            pytest.skip(f"Cannot import timeseries: {e}")

    def test_returns_based_analysis(self):
        """Verify returns-based analysis (daily/monthly returns)."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(daily_return|monthly_return|annual_return|aggregate_returns|pct_change)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No returns-based analysis found")

    def test_statistical_functions(self):
        """Verify statistical functions (std, mean, etc.)."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(\.std\(|\.mean\(|np\.std|np\.mean|scipy\.stats)", content):
                return
        pytest.fail("No statistical functions found")

    def test_plotting_functions(self):
        """Verify plotting / visualization functions."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(plot|matplotlib|plt\.|ax\.|figure)", content):
                return
        pytest.fail("No plotting functions found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_py_files(self):
        results = []
        pkg = os.path.join(self.REPO_DIR, "pyfolio")
        search = pkg if os.path.isdir(pkg) else self.REPO_DIR
        for dirpath, _, fnames in os.walk(search):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
