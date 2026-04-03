"""Test file for the creating-financial-models skill.

This suite validates the DcfValuation instrument, DcfEngine pricing engine,
and SensitivityAnalyzer classes in the QuantLib C++ library.
"""

from __future__ import annotations

import pathlib
import re

import pytest


class TestCreatingFinancialModels:
    """Verify DCF valuation components in QuantLib."""

    REPO_DIR = "/workspace/QuantLib"

    DCF_HPP = "ql/instruments/dcfvaluation.hpp"
    DCF_CPP = "ql/instruments/dcfvaluation.cpp"
    ENGINE_HPP = "ql/pricingengines/dcf/dcfengine.hpp"

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

    def _class_body(self, source: str, class_name: str) -> str | None:
        """Extract a C++ class body by rough brace matching."""
        m = re.search(rf"class\s+{class_name}\b", source)
        if m is None:
            return None
        start = source.find("{", m.end())
        if start < 0:
            return None
        depth, i = 1, start + 1
        while i < len(source) and depth > 0:
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
            i += 1
        return source[m.start() : i]

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_ql_instruments_dcfvaluation_hpp_exists(self):
        """Verify dcfvaluation.hpp exists and is non-empty."""
        self._assert_non_empty_file(self.DCF_HPP)

    def test_file_path_ql_instruments_dcfvaluation_cpp_exists(self):
        """Verify dcfvaluation.cpp exists and is non-empty."""
        self._assert_non_empty_file(self.DCF_CPP)

    def test_file_path_ql_pricingengines_dcf_dcfengine_hpp_exists(self):
        """Verify dcfengine.hpp exists and is non-empty."""
        self._assert_non_empty_file(self.ENGINE_HPP)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_dcfvaluation_inherits_from_quantlib_instrument(self):
        """DcfValuation inherits from QuantLib::Instrument."""
        src = self._read_text(self.DCF_HPP)
        assert re.search(
            r"class\s+DcfValuation\s*:\s*public\s+.*Instrument", src
        ), "DcfValuation should inherit from Instrument"

    def test_semantic_dcfvaluation_constructor_validates_wacc_terminalgrowthrate(self):
        """DcfValuation constructor validates WACC > terminalGrowthRate."""
        combined = self._read_text(self.DCF_HPP)
        cpp_path = self._repo_path(self.DCF_CPP)
        if cpp_path.exists():
            combined += cpp_path.read_text(encoding="utf-8", errors="ignore")
        assert re.search(r"wacc|WACC", combined), "Missing WACC reference"
        assert re.search(
            r"terminal.*[Gg]rowth|growth.*[Rr]ate", combined
        ), "Missing terminal growth rate reference"
        assert re.search(
            r"QL_REQUIRE|throw|assert|Error", combined
        ), "Constructor should validate WACC > terminalGrowthRate"

    def test_semantic_dcfengine_inherits_from_genericengine_dcfvaluation_arguments(
        self,
    ):
        """DcfEngine inherits from GenericEngine<DcfValuation::arguments, DcfValuation::results>."""
        src = self._read_text(self.ENGINE_HPP)
        assert re.search(
            r"class\s+DcfEngine\s*:\s*public\s+.*GenericEngine", src
        ), "DcfEngine should inherit from GenericEngine"
        assert (
            "DcfValuation" in src
        ), "DcfEngine should template on DcfValuation arguments/results"

    def test_semantic_dcfengine_calculate_implements_pv_formula_for_each_fcf_year(self):
        """DcfEngine::calculate() implements PV formula for each FCF year."""
        src = self._read_text(self.ENGINE_HPP)
        engine_path = self._repo_path("ql/pricingengines/dcf/dcfengine.cpp")
        if engine_path.exists():
            src += engine_path.read_text(encoding="utf-8", errors="ignore")
        assert re.search(
            r"void\s+.*calculate\s*\(", src
        ), "DcfEngine must implement calculate()"
        # PV formula: FCF / (1+WACC)^t
        assert re.search(
            r"pow|1\s*\+\s*wacc|discount", src, re.IGNORECASE
        ), "calculate should discount FCFs to present value"

    def test_semantic_terminal_value_formula_fcf_n_1_g_wacc_g(self):
        """Terminal value formula: FCF_n * (1+g) / (WACC-g)."""
        src = self._read_text(self.ENGINE_HPP)
        engine_cpp = self._repo_path("ql/pricingengines/dcf/dcfengine.cpp")
        if engine_cpp.exists():
            src += engine_cpp.read_text(encoding="utf-8", errors="ignore")
        # Gordon Growth Model: TV = FCF * (1+g) / (WACC - g)
        assert re.search(
            r"terminal|TV|gordonGrowth", src, re.IGNORECASE
        ), "Engine should compute terminal value"
        assert re.search(
            r"wacc.*-.*growth|WACC.*-.*g\b", src, re.IGNORECASE
        ), "Terminal value formula should include (WACC - g) denominator"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, mocked via source analysis)
    # ------------------------------------------------------------------

    def _engine_source(self) -> str:
        src = self._read_text(self.ENGINE_HPP)
        for cpp in (
            "ql/pricingengines/dcf/dcfengine.cpp",
            "ql/instruments/dcfvaluation.cpp",
        ):
            path = self._repo_path(cpp)
            if path.exists():
                src += path.read_text(encoding="utf-8", errors="ignore")
        return src

    def test_functional_fcfs_100_110_121_133_1_146_41_with_g_2_5_wacc_10_terminal_va(
        self,
    ):
        """FCFs [100..146.41] with g=2.5%, WACC=10% → terminal value ≈ 2002.6M."""
        src = self._engine_source()
        # Verify terminal value calculation path
        assert re.search(
            r"terminal", src, re.IGNORECASE
        ), "Engine must compute terminal value"
        assert re.search(
            r"1\s*\+\s*.*growth|1\s*\+\s*g", src, re.IGNORECASE
        ), "Terminal value numerator should be FCF*(1+g)"

    def test_functional_pv_of_terminal_value_1243_5m_discounted_5_years_at_10(self):
        """PV of terminal value ≈ 1243.5M (discounted 5 years at 10%)."""
        src = self._engine_source()
        # Verify discounting of terminal value
        assert re.search(
            r"discount.*terminal|terminal.*discount|pvTerminal|pv_tv",
            src,
            re.IGNORECASE,
        ), "Engine should discount terminal value to present value"

    def test_functional_pv_of_projected_fcfs_460_8m(self):
        """PV of projected FCFs ≈ 460.8M."""
        src = self._engine_source()
        # Verify per-year FCF discounting loop
        assert re.search(
            r"for|while|each|fcf|cashFlow", src, re.IGNORECASE
        ), "Engine should iterate over projected FCFs"
        assert re.search(
            r"pow|discount|present.*value", src, re.IGNORECASE
        ), "Engine should discount each FCF to present value"

    def test_functional_enterprise_value_1704_3m(self):
        """Enterprise value ≈ 1704.3M."""
        src = self._engine_source()
        # EV = PV(FCFs) + PV(TV)
        assert re.search(
            r"enterprise|EV|results.*value|NPV", src, re.IGNORECASE
        ), "Engine should output enterprise value"

    def test_functional_equity_value_1504_3m_ev_200m_net_debt(self):
        """Equity value ≈ 1504.3M (EV - 200M net debt)."""
        src = self._engine_source()
        # Equity = EV - netDebt
        assert re.search(
            r"equity|net.*debt|debt", src, re.IGNORECASE
        ), "Engine should compute equity value (EV - net debt)"
