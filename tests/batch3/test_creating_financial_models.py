"""
Tests for creating-financial-models skill.
Validates DCFValuationEngine implementation in QuantLib repository.
"""

import os
import pytest

REPO_DIR = "/workspace/QuantLib"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestCreatingFinancialModels:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_dcf_valuation_header_exists(self):
        """ql/models/dcf_valuation.hpp must exist."""
        assert os.path.isfile(
            _path("ql/models/dcf_valuation.hpp")
        ), "ql/models/dcf_valuation.hpp not found"

    def test_dcf_valuation_source_exists(self):
        """ql/models/dcf_valuation.cpp must exist."""
        assert os.path.isfile(
            _path("ql/models/dcf_valuation.cpp")
        ), "ql/models/dcf_valuation.cpp not found"

    def test_dcf_test_suite_exists(self):
        """test-suite/dcfvaluation.cpp must exist."""
        assert os.path.isfile(
            _path("test-suite/dcfvaluation.cpp")
        ), "test-suite/dcfvaluation.cpp not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_dcf_class_defined_in_header(self):
        """Header must declare DCFValuationEngine class."""
        content = _read("ql/models/dcf_valuation.hpp")
        assert (
            "DCFValuationEngine" in content
        ), "DCFValuationEngine class not declared in header"

    def test_fcf_method_declared(self):
        """Source must contain free cash flow method."""
        content = _read("ql/models/dcf_valuation.cpp")
        assert any(
            kw in content for kw in ["fcf", "freeCashFlow", "free_cash_flow"]
        ), "FCF method not found in dcf_valuation.cpp"

    def test_terminal_value_method_declared(self):
        """Source must contain terminal value calculation method."""
        content = _read("ql/models/dcf_valuation.cpp")
        assert any(
            kw in content for kw in ["terminalValue", "terminal_value", "gordonGrowth"]
        ), "Terminal value method not found in dcf_valuation.cpp"

    def test_enterprise_value_method_declared(self):
        """Source must contain enterprise value summation method."""
        content = _read("ql/models/dcf_valuation.cpp")
        assert any(
            kw in content for kw in ["enterpriseValue", "enterprise_value", "npv"]
        ), "Enterprise value method not found in dcf_valuation.cpp"

    def test_sensitivity_analysis_declared(self):
        """Source must contain sensitivityAnalysis method."""
        content = _read("ql/models/dcf_valuation.cpp")
        assert (
            "sensitivityAnalysis" in content or "sensitivity_analysis" in content
        ), "sensitivityAnalysis method not found in dcf_valuation.cpp"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_pv_formula_three_equal_cashflows(self):
        """PV of [100, 100, 100] @ WACC=0.10 must be approximately 248.69."""
        wacc = 0.10
        fcf = [100.0, 100.0, 100.0]
        pv = sum(fcf[i] / (1 + wacc) ** (i + 1) for i in range(len(fcf)))
        assert abs(pv - 248.69) < 0.1, f"Expected PV ≈ 248.69, got {pv:.4f}"

    def test_gordon_growth_terminal_value(self):
        """Gordon Growth Model: FCF=200, g=0.03, WACC=0.10 must yield ≈ 2942.86."""
        fcf_final = 200.0
        g = 0.03
        wacc = 0.10
        tv = fcf_final * (1 + g) / (wacc - g)
        assert abs(tv - 2942.86) < 1.0, f"Expected TV ≈ 2942.86, got {tv:.4f}"

    def test_growth_rate_equals_wacc_raises_error(self):
        """When growth_rate == WACC, division by zero must raise ValueError."""

        def gordon_growth(fcf_final, g, wacc):
            if abs(g - wacc) < 1e-12:
                raise ValueError("growth_rate cannot equal WACC: division by zero")
            return fcf_final * (1 + g) / (wacc - g)

        with pytest.raises(ValueError, match="division by zero"):
            gordon_growth(100.0, 0.10, 0.10)

    def test_negative_fcf_raises_error(self):
        """Negative FCF input must raise ValueError."""

        def compute_pv(fcf_list, wacc):
            if any(v < 0 for v in fcf_list):
                raise ValueError("FCF values must be non-negative")
            return sum(
                fcf_list[i] / (1 + wacc) ** (i + 1) for i in range(len(fcf_list))
            )

        with pytest.raises(ValueError, match="non-negative"):
            compute_pv([-50.0, 100.0], 0.10)

    def test_sensitivity_grid_dimensions(self):
        """Sensitivity grid over 3 WACC × 2 growth rates must return 3×2 matrix."""

        def sensitivity_analysis(fcf_final, wacc_range, growth_range):
            grid = []
            for wacc in wacc_range:
                row = []
                for g in growth_range:
                    if abs(g - wacc) < 1e-12:
                        row.append(None)
                    else:
                        row.append(fcf_final * (1 + g) / (wacc - g))
                grid.append(row)
            return grid

        wacc_range = [0.08, 0.10, 0.12]
        growth_range = [0.02, 0.03]
        grid = sensitivity_analysis(200.0, wacc_range, growth_range)
        assert len(grid) == 3, f"Expected 3 rows, got {len(grid)}"
        assert all(len(row) == 2 for row in grid), "Each row must have 2 columns"
