"""
Test for 'risk-metrics-calculation' skill — Risk Metrics Calculation
Validates that the Agent created a risk metrics demo for pyfolio computing
VaR, CVaR, Sharpe ratio, Sortino ratio, and maximum drawdown.
"""

import os
import re
import subprocess

import pytest



class TestRiskMetricsCalculation:
    """Verify risk metrics calculation demo for pyfolio."""

    REPO_DIR = "/workspace/pyfolio"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence and syntax
    # ------------------------------------------------------------------

    def test_demo_file_exists(self):
        """examples/risk_metrics_demo.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "examples", "risk_metrics_demo.py")
        assert os.path.isfile(fpath), "examples/risk_metrics_demo.py not found"

    def test_demo_compiles(self):
        """risk_metrics_demo.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "examples/risk_metrics_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_demo_has_main_entry_point(self):
        """Script must have a __main__ entry point."""
        content = self._read("examples", "risk_metrics_demo.py")
        assert re.search(
            r'if\s+__name__\s*==\s*["\']__main__["\']', content
        ), "Missing __main__ entry point"

    # ------------------------------------------------------------------
    # L1: All five metrics present
    # ------------------------------------------------------------------

    def test_computes_var(self):
        """Script must compute Value at Risk (VaR)."""
        content = self._read("examples", "risk_metrics_demo.py")
        patterns = [
            r"[Vv]a[Rr]",
            r"value.at.risk",
            r"value_at_risk",
            r"quantile",
            r"percentile",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not compute VaR"

    def test_computes_cvar(self):
        """Script must compute Conditional VaR (CVaR / Expected Shortfall)."""
        content = self._read("examples", "risk_metrics_demo.py")
        patterns = [
            r"[Cc][Vv]a[Rr]",
            r"expected.shortfall",
            r"conditional.*value.*risk",
            r"tail.*mean",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not compute CVaR / Expected Shortfall"

    def test_computes_sharpe_ratio(self):
        """Script must compute Sharpe ratio."""
        content = self._read("examples", "risk_metrics_demo.py")
        assert re.search(r"[Ss]harpe", content), "Script does not compute Sharpe ratio"

    def test_computes_sortino_ratio(self):
        """Script must compute Sortino ratio."""
        content = self._read("examples", "risk_metrics_demo.py")
        assert re.search(
            r"[Ss]ortino", content
        ), "Script does not compute Sortino ratio"

    def test_computes_max_drawdown(self):
        """Script must compute maximum drawdown."""
        content = self._read("examples", "risk_metrics_demo.py")
        patterns = [r"max.*drawdown", r"maximum.*drawdown", r"drawdown"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not compute maximum drawdown"

    # ------------------------------------------------------------------
    # L1: Configuration parameters
    # ------------------------------------------------------------------

    def test_configurable_confidence_level(self):
        """VaR/CVaR must support configurable confidence levels."""
        content = self._read("examples", "risk_metrics_demo.py")
        patterns = [r"confidence", r"alpha", r"0\.95", r"0\.99", r"95", r"99"]
        assert any(
            re.search(p, content) for p in patterns
        ), "VaR/CVaR confidence level is not configurable"

    def test_configurable_risk_free_rate(self):
        """Sharpe ratio must accept a risk-free rate parameter."""
        content = self._read("examples", "risk_metrics_demo.py")
        patterns = [r"risk.free", r"rf_rate", r"risk_free_rate", r"rf"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Sharpe ratio missing risk-free rate parameter"

    # ------------------------------------------------------------------
    # L2: Input validation
    # ------------------------------------------------------------------

    def test_validates_inputs(self):
        """Script must validate inputs (reject empty series, invalid confidence)."""
        content = self._read("examples", "risk_metrics_demo.py")
        validation_patterns = [
            r"raise\s+ValueError",
            r"raise\s+TypeError",
            r"if\s+len\(",
            r"if\s+not\s+",
            r"empty",
            r"assert\s+",
            r"validate",
        ]
        assert any(
            re.search(p, content) for p in validation_patterns
        ), "Script does not validate inputs"

    # ------------------------------------------------------------------
    # L2: Dynamic execution
    # ------------------------------------------------------------------

    def test_script_runs_successfully(self):
        """risk_metrics_demo.py must run to completion."""
        result = subprocess.run(
            ["python", "examples/risk_metrics_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert (
            result.returncode == 0
        ), f"Script failed:\nstderr: {result.stderr[-2000:]}"

    def test_output_contains_all_metrics(self):
        """Script output must contain all five metric results."""
        result = subprocess.run(
            ["python", "examples/risk_metrics_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = (result.stdout + result.stderr).lower()
        metrics = ["var", "cvar", "sharpe", "sortino", "drawdown"]
        found = [m for m in metrics if m in output]
        missing = [m for m in metrics if m not in output]
        assert (
            len(found) >= 4
        ), f"Output missing metric results. Found: {found}, Missing: {missing}"

    def test_output_contains_numeric_values(self):
        """Script output must contain actual numeric metric values, not just labels."""
        result = subprocess.run(
            ["python", "examples/risk_metrics_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout
        numbers = re.findall(r"-?\d+\.?\d*", output)
        assert len(numbers) >= 5, (
            f"Output contains only {len(numbers)} numeric values — "
            f"expected at least 5 metric results"
        )
