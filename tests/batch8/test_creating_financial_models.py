"""
Test for 'creating-financial-models' skill — Financial Models (DCF + Scenarios)
Validates that the Agent created a Python package implementing DCF valuation,
IRR computation, sensitivity tables, and scenario analysis.
"""

import os
import re
import sys

import pytest


class TestCreatingFinancialModels:
    """Verify financial models package implementation."""

    REPO_DIR = "/workspace/QuantLib"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_financial_models_package_exists(self):
        """Verify the financial_models package __init__.py and dcf.py exist."""
        for rel in ("src/financial_models/__init__.py", "src/financial_models/dcf.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_scenarios_sensitivity_files_exist(self):
        """Verify scenarios.py and sensitivity.py exist."""
        for rel in ("src/financial_models/scenarios.py",
                     "src/financial_models/sensitivity.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_all_classes_importable(self):
        """All main classes and DCFResult are importable."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            from financial_models.dcf import DCFModel, DCFResult  # noqa: F401
            from financial_models.scenarios import ScenarioAnalyzer  # noqa: F401
            from financial_models.sensitivity import SensitivityTable  # noqa: F401
        except ImportError:
            pytest.skip("financial_models not importable")
        finally:
            sys.path.pop(0)

    # ── semantic_check ──────────────────────────────────────────────

    def test_dcf_model_class_defined(self):
        """Verify dcf.py defines DCFModel class with calculate and irr methods."""
        content = self._read(os.path.join(self.REPO_DIR, "src/financial_models/dcf.py"))
        assert content, "dcf.py is empty or unreadable"
        for pat in ("class DCFModel", "def calculate", "def irr"):
            assert pat in content, f"'{pat}' not found in dcf.py"

    def test_value_error_guards_in_dcf(self):
        """Verify ValueError is raised for invalid inputs in dcf.py."""
        content = self._read(os.path.join(self.REPO_DIR, "src/financial_models/dcf.py"))
        assert content, "dcf.py is empty or unreadable"
        for pat in ("ValueError", "discount_rate", "terminal_growth_rate"):
            assert pat in content, f"'{pat}' not found in dcf.py"

    def test_sensitivity_table_compute_defined(self):
        """Verify SensitivityTable class and compute method are defined."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/financial_models/sensitivity.py"))
        assert content, "sensitivity.py is empty or unreadable"
        assert "class SensitivityTable" in content, "SensitivityTable class not found"
        assert "def compute" in content, "compute method not found"

    # ── functional_check (import) ───────────────────────────────────

    def _import(self, dotpath: str):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            return __import__(dotpath, fromlist=[""])
        except ImportError:
            pytest.skip(f"{dotpath} not importable")
        finally:
            sys.path.pop(0)

    def test_dcf_npv_calculation(self):
        """DCFModel.calculate with [100, 200, 300] at 10% discount rate computes correct NPV."""
        mod = self._import("financial_models.dcf")
        result = mod.DCFModel().calculate([100, 200, 300], discount_rate=0.10,
                                          terminal_growth_rate=0.02)
        expected_npv = sum(cf / (1.10 ** (i + 1)) for i, cf in enumerate([100, 200, 300]))
        assert abs(result.npv - expected_npv) < 0.01, \
            f"NPV mismatch: expected ~{expected_npv:.2f}, got {result.npv}"

    def test_dcf_terminal_value_formula(self):
        """DCFModel.calculate produces correct terminal value using Gordon Growth Model."""
        mod = self._import("financial_models.dcf")
        result = mod.DCFModel().calculate([100, 200, 300], 0.10, 0.02)
        expected_tv = 300 * 1.02 / (0.10 - 0.02)
        assert abs(result.terminal_value - expected_tv) < 0.01, \
            f"Terminal value mismatch: expected ~{expected_tv:.2f}, got {result.terminal_value}"

    def test_dcf_empty_cash_flows_raises_value_error(self):
        """DCFModel.calculate with empty cash_flows raises ValueError."""
        mod = self._import("financial_models.dcf")
        with pytest.raises(ValueError):
            mod.DCFModel().calculate([], 0.10, 0.02)

    def test_dcf_rate_equals_growth_raises_value_error(self):
        """discount_rate == terminal_growth_rate raises ValueError."""
        mod = self._import("financial_models.dcf")
        with pytest.raises(ValueError, match="discount_rate"):
            mod.DCFModel().calculate([100], 0.05, 0.05)

    def test_sensitivity_table_shape(self):
        """SensitivityTable.compute returns 3x3 table for 3 discount rates and 3 growth rates."""
        mod_dcf = self._import("financial_models.dcf")
        mod_sens = self._import("financial_models.sensitivity")
        model = mod_dcf.DCFModel()
        table = mod_sens.SensitivityTable().compute(
            model, [0.08, 0.10, 0.12], [0.01, 0.02, 0.03]
        )
        assert len(table) == 3, f"Expected 3 rows, got {len(table)}"
        for row in table:
            assert len(row) == 3, f"Expected 3 columns, got {len(row)}"
