"""
Test for 'slo-implementation' skill — Multi-Window SLO Evaluation
Validates that the Agent created multi-window SLO evaluation and burn rate
logic for the slo-generator project.
"""

import os
import re
import subprocess

import pytest


class TestSloImplementation:
    """Verify multi-window SLO evaluation and burn rate implementation."""

    REPO_DIR = "/workspace/slo-generator"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence and syntax
    # ------------------------------------------------------------------

    def test_multi_window_exists(self):
        """slo_generator/multi_window.py must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "slo_generator", "multi_window.py")
        )

    def test_burn_rate_exists(self):
        """slo_generator/burn_rate.py must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "slo_generator", "burn_rate.py")
        )

    def test_multi_window_compiles(self):
        """multi_window.py must be syntactically valid."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "slo_generator/multi_window.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_burn_rate_compiles(self):
        """burn_rate.py must be syntactically valid."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "slo_generator/burn_rate.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L1: Multi-window evaluation basics
    # ------------------------------------------------------------------

    def test_multi_window_accepts_multiple_windows(self):
        """multi_window.py must accept multiple compliance windows."""
        content = self._read("slo_generator", "multi_window.py")
        patterns = [
            r"windows",
            r"\[.*1h.*1d.*30d\]",
            r"window.*list",
            r"List\[",
            r"multiple.*window",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "multi_window.py does not accept multiple windows"

    def test_multi_window_computes_sli(self):
        """multi_window.py must compute SLI values."""
        content = self._read("slo_generator", "multi_window.py")
        patterns = [
            r"sli",
            r"SLI",
            r"service_level_indicator",
            r"good.*total",
            r"success.*total",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "multi_window.py does not compute SLI"

    def test_multi_window_calculates_error_budget(self):
        """multi_window.py must calculate error budget remaining."""
        content = self._read("slo_generator", "multi_window.py")
        patterns = [
            r"error.budget",
            r"budget.*remaining",
            r"ErrorBudget",
            r"error_budget",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "multi_window.py does not calculate error budget"

    def test_multi_window_returns_per_window_results(self):
        """multi_window.py must return per-window metrics."""
        content = self._read("slo_generator", "multi_window.py")
        patterns = [
            r"per.window",
            r"for.*window",
            r"results\[",
            r"window.*result",
            r"append.*result",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "multi_window.py does not return per-window results"

    # ------------------------------------------------------------------
    # L2: Error budget formula
    # ------------------------------------------------------------------

    def test_error_budget_formula(self):
        """Error budget formula: 1 - (1 - SLI) / (1 - SLO_target)."""
        content = self._read("slo_generator", "multi_window.py")
        # Look for the formula pattern
        patterns = [
            r"1\s*-\s*\(1\s*-\s*sli\)\s*/\s*\(1\s*-\s*",
            r"error_rate.*allowed_error",
            r"budget.*remaining",
            r"consumed.*budget",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Error budget formula not implemented correctly"

    def test_flags_exhausted_budget(self):
        """Code must flag windows where error budget is exhausted."""
        combined = self._read("slo_generator", "multi_window.py") + self._read(
            "slo_generator", "burn_rate.py"
        )
        patterns = [
            r"exhaust",
            r"remaining.*<=.*0",
            r"budget.*0",
            r"depleted",
            r"violated",
            r"breached",
        ]
        assert any(
            re.search(p, combined, re.IGNORECASE) for p in patterns
        ), "Code does not flag exhausted error budgets"

    # ------------------------------------------------------------------
    # L2: Burn rate
    # ------------------------------------------------------------------

    def test_burn_rate_calculation(self):
        """burn_rate.py must calculate burn rate."""
        content = self._read("slo_generator", "burn_rate.py")
        patterns = [r"burn.*rate", r"BurnRate", r"burn_rate"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "burn_rate.py does not calculate burn rate"

    def test_fast_burn_condition(self):
        """burn_rate.py must define fast-burn alert condition."""
        content = self._read("slo_generator", "burn_rate.py")
        patterns = [
            r"fast.*burn",
            r"FastBurn",
            r"fast_burn",
            r"short.*window.*high.*rate",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "burn_rate.py does not define fast-burn condition"

    def test_slow_burn_condition(self):
        """burn_rate.py must define slow-burn alert condition."""
        content = self._read("slo_generator", "burn_rate.py")
        patterns = [r"slow.*burn", r"SlowBurn", r"slow_burn", r"long.*window.*elevated"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "burn_rate.py does not define slow-burn condition"

    def test_combined_alert_logic(self):
        """Alert fires only when both fast and slow burn conditions met."""
        content = self._read("slo_generator", "burn_rate.py")
        patterns = [
            r"fast.*and.*slow",
            r"both",
            r"fast_burn.*slow_burn",
            r"alert.*fire",
            r"should_alert",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "No combined fast+slow burn alert logic found"

    def test_overall_compliance_summary(self):
        """Code must provide an overall compliance summary."""
        combined = self._read("slo_generator", "multi_window.py") + self._read(
            "slo_generator", "burn_rate.py"
        )
        patterns = [r"summary", r"compliance", r"overall", r"status", r"report"]
        assert any(
            re.search(p, combined, re.IGNORECASE) for p in patterns
        ), "No overall compliance summary found"
