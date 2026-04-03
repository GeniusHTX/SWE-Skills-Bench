"""
Test for 'creating-financial-models' skill — DCF Valuation Model
Validates that the Agent created a DCFModel and SensitivityAnalysis
with proper financial calculations in the QuantLib project.
"""

import os
import sys

import pytest


class TestCreatingFinancialModels:
    """Verify DCF financial model implementation in QuantLib."""

    REPO_DIR = "/workspace/QuantLib"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _import_dcf(self):
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from Python.examples.dcf_valuation import (
                DCFModel,
                SensitivityAnalysis,
            )

            return DCFModel, SensitivityAnalysis
        finally:
            sys.path[:] = old_path

    # ---- file_path_check ----

    def test_dcf_valuation_exists(self):
        """Verifies Python/examples/dcf_valuation.py exists."""
        path = os.path.join(self.REPO_DIR, "Python/examples/dcf_valuation.py")
        assert os.path.exists(path), f"File not found: {path}"

    def test_requirements_exists(self):
        """Verifies Python/examples/requirements.txt exists."""
        path = os.path.join(self.REPO_DIR, "Python/examples/requirements.txt")
        assert os.path.exists(path), f"File not found: {path}"

    # ---- semantic_check ----

    def test_sem_imports(self):
        """Verifies DCFModel and SensitivityAnalysis are importable."""
        DCFModel, SensitivityAnalysis = self._import_dcf()
        assert DCFModel is not None
        assert SensitivityAnalysis is not None

    def test_sem_dcfmodel_methods(self):
        """Verifies DCFModel has calculate_dcf, calculate_wacc, sensitivity_analysis."""
        text = self._read(
            os.path.join(self.REPO_DIR, "Python/examples/dcf_valuation.py")
        )
        for method in ["calculate_dcf", "calculate_wacc", "sensitivity_analysis"]:
            assert method in text, f"DCFModel missing method: {method}"

    def test_sem_sensitivity_methods(self):
        """Verifies SensitivityAnalysis has run and tornado_chart_data."""
        text = self._read(
            os.path.join(self.REPO_DIR, "Python/examples/dcf_valuation.py")
        )
        assert "def run" in text, "SensitivityAnalysis missing 'run' method"
        assert "tornado_chart_data" in text, "Missing tornado_chart_data"

    def test_sem_return_keys(self):
        """Verifies calculate_dcf returns pv_cash_flows, terminal_value, enterprise_value."""
        text = self._read(
            os.path.join(self.REPO_DIR, "Python/examples/dcf_valuation.py")
        )
        for key in ["pv_cash_flows", "terminal_value", "enterprise_value"]:
            assert key in text, f"Missing return key: {key}"

    def test_sem_numeric_types(self):
        """Verifies float or Decimal used for monetary values."""
        text = self._read(
            os.path.join(self.REPO_DIR, "Python/examples/dcf_valuation.py")
        )
        assert "float" in text or "Decimal" in text, "No numeric type annotations found"

    # ---- functional_check ----

    def test_func_dcf_enterprise_value(self):
        """Verifies DCF calculation with [100,100,100], rate=0.10, growth=0.02."""
        DCFModel, _ = self._import_dcf()
        result = DCFModel().calculate_dcf([100, 100, 100], 0.10, 0.02)
        ev = result["enterprise_value"]
        # Expected: sum(100/(1.1**t) for t in 1..3) + (100*1.02/0.08)/(1.1**3)
        expected_pv = sum(100 / (1.1**t) for t in range(1, 4))
        terminal = (100 * 1.02 / 0.08) / (1.1**3)
        expected = expected_pv + terminal
        assert (
            abs(ev - expected) / expected < 0.05
        ), f"Enterprise value {ev} not close to expected {expected}"

    def test_func_wacc(self):
        """Verifies WACC calculation: equity=600, debt=400, re=0.12, rd=0.08, tax=0.25."""
        DCFModel, _ = self._import_dcf()
        wacc = DCFModel().calculate_wacc(600, 400, 0.12, 0.08, 0.25)
        # Expected: (600/1000)*0.12 + (400/1000)*0.08*(1-0.25) = 0.072 + 0.024 = 0.096
        assert abs(wacc - 0.096) < 0.01, f"WACC {wacc} not close to 0.096"

    def test_func_pv_cash_flows(self):
        """Verifies PV of single cash flow [100] at rate 0.10."""
        DCFModel, _ = self._import_dcf()
        result = DCFModel().calculate_dcf([100], 0.10, 0.02)
        pv = result["pv_cash_flows"]
        assert abs(pv[0] - 90.909) < 1.0, f"PV {pv[0]} not ~90.909"

    def test_func_terminal_value(self):
        """Verifies terminal value for [100] at rate 0.10, growth 0.02."""
        DCFModel, _ = self._import_dcf()
        result = DCFModel().calculate_dcf([100], 0.10, 0.02)
        tv = result["terminal_value"]
        expected_tv = 100 * 1.02 / 0.08  # = 1275
        assert abs(tv - expected_tv) < 10, f"TV {tv} not close to {expected_tv}"

    def test_func_empty_cashflows_raises(self):
        """Failure: empty cash flows raises ValueError."""
        DCFModel, _ = self._import_dcf()
        with pytest.raises(ValueError):
            DCFModel().calculate_dcf([], 0.10, 0.02)

    def test_func_rate_equals_growth_raises(self):
        """Failure: rate == growth raises ValueError."""
        DCFModel, _ = self._import_dcf()
        with pytest.raises(ValueError):
            DCFModel().calculate_dcf([100], 0.10, 0.10)

    def test_func_rate_less_than_growth_raises(self):
        """Failure: rate < growth raises ValueError."""
        DCFModel, _ = self._import_dcf()
        with pytest.raises(ValueError):
            DCFModel().calculate_dcf([100], 0.08, 0.10)

    def test_func_zero_rate_raises(self):
        """Failure: non-positive rate raises ValueError."""
        DCFModel, _ = self._import_dcf()
        with pytest.raises(ValueError):
            DCFModel().calculate_dcf([100], 0.0, 0.02)
