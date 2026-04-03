"""
Test for 'risk-metrics-calculation' skill — Risk metrics with pyfolio
Validates that the Agent implemented risk metrics calculation including
Sharpe ratio, VaR, drawdown analysis using pyfolio.
"""

import os
import re

import pytest


class TestRiskMetricsCalculation:
    """Verify risk metrics calculation with pyfolio."""

    REPO_DIR = "/workspace/pyfolio"

    def test_sharpe_ratio_calculation(self):
        """Sharpe ratio must be calculated."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Ss]harpe|sharpe_ratio|annual_return.*std", content):
                        found = True
                        break
            if found:
                break
        assert found, "No Sharpe ratio calculation found"

    def test_var_calculation(self):
        """Value at Risk (VaR) must be calculated."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Vv]a[Rr]|value.at.risk|var_|quantile|percentile", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No VaR calculation found"

    def test_drawdown_analysis(self):
        """Maximum drawdown analysis must be implemented."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Dd]rawdown|max_drawdown|drawdown_peaks", content):
                        found = True
                        break
            if found:
                break
        assert found, "No drawdown analysis found"

    def test_returns_calculation(self):
        """Returns calculation must be implemented."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"returns|annual_return|cumulative|pct_change|log_return", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No returns calculation found"

    def test_volatility_calculation(self):
        """Volatility calculation must be implemented."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Vv]olatility|annual.*vol|std|annualized_vol", content):
                        found = True
                        break
            if found:
                break
        assert found, "No volatility calculation found"

    def test_pandas_usage(self):
        """pandas must be used for data manipulation."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"import\s+pandas|from\s+pandas|pd\.", content):
                        found = True
                        break
            if found:
                break
        assert found, "No pandas usage found"

    def test_tear_sheet_or_report(self):
        """Tear sheet or performance report generation must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"tear.?sheet|create_.*returns|perf_stats|report|summary", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No tear sheet or report generation found"

    def test_benchmark_comparison(self):
        """Benchmark comparison should be supported."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"benchmark|factor_returns|alpha|beta|excess_return", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No benchmark comparison found"

    def test_plotting_or_visualization(self):
        """Plots or visualizations must be generated."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"plot|matplotlib|plt\.|figure|ax\.|subplot", content):
                        found = True
                        break
            if found:
                break
        assert found, "No plotting found"

    def test_sortino_or_calmar_ratio(self):
        """Additional risk ratios (Sortino, Calmar) should be calculated."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Ss]ortino|[Cc]almar|[Oo]mega|downside.*risk|information.ratio", content):
                        found = True
                        break
            if found:
                break
        assert found, "No additional risk ratios found"
