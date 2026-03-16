"""
Test for 'risk-metrics-calculation' skill — Risk Metrics Calculation
Validates that the Agent implemented risk metric calculations (Sharpe, Max Drawdown,
Sortino, Calmar) with example scripts and tests in pyfolio.
"""

import os
import subprocess
import json
import pytest


class TestRiskMetricsCalculation:
    """Verify risk metrics calculation implementation in pyfolio."""

    REPO_DIR = "/workspace/pyfolio"

    # ------------------------------------------------------------------
    # L1: file existence & syntax
    # ------------------------------------------------------------------

    def test_demo_script_exists(self):
        """examples/risk_metrics_demo.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "examples", "risk_metrics_demo.py")
        assert os.path.isfile(fpath), "risk_metrics_demo.py not found"

    def test_demo_script_compiles(self):
        """Demo script must compile."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "examples/risk_metrics_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: runtime & content verification
    # ------------------------------------------------------------------

    def test_demo_script_runs(self):
        """Demo script must run and exit with code 0."""
        result = subprocess.run(
            ["python", "examples/risk_metrics_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"Demo failed:\n{result.stderr}"

    def test_demo_produces_output(self):
        """Demo must produce non-empty output."""
        result = subprocess.run(
            ["python", "examples/risk_metrics_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert len(result.stdout.strip()) > 0, "Demo produced no output"

    def test_sharpe_ratio_in_source(self):
        """Demo must calculate Sharpe ratio."""
        fpath = os.path.join(self.REPO_DIR, "examples", "risk_metrics_demo.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert "sharpe" in content.lower(), "Sharpe ratio calculation not found"

    def test_max_drawdown_in_source(self):
        """Demo must calculate maximum drawdown."""
        fpath = os.path.join(self.REPO_DIR, "examples", "risk_metrics_demo.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert "drawdown" in content.lower(), "Max drawdown calculation not found"

    def test_sortino_ratio_in_source(self):
        """Demo must calculate Sortino ratio."""
        fpath = os.path.join(self.REPO_DIR, "examples", "risk_metrics_demo.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert "sortino" in content.lower(), "Sortino ratio calculation not found"

    def test_calmar_ratio_in_source(self):
        """Demo must calculate Calmar ratio."""
        fpath = os.path.join(self.REPO_DIR, "examples", "risk_metrics_demo.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert "calmar" in content.lower(), "Calmar ratio calculation not found"

    def test_output_contains_numeric_metrics(self):
        """Demo output must contain numeric metric values."""
        result = subprocess.run(
            ["python", "examples/risk_metrics_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"Demo failed: {result.stderr[:500]}")
        output = result.stdout
        import re

        numbers = re.findall(r"-?\d+\.\d+", output)
        assert (
            len(numbers) >= 2
        ), f"Expected numeric metric values in output, found {len(numbers)} numbers"

    def test_output_or_file_has_json_csv(self):
        """Demo should produce JSON or CSV format output."""
        fpath = os.path.join(self.REPO_DIR, "examples", "risk_metrics_demo.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        output_formats = ["json", "csv", "to_json", "to_csv", "json.dump", "DictWriter"]
        found = any(fmt in content.lower() for fmt in output_formats)
        assert found, "No JSON/CSV output generation found in demo script"
