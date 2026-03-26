"""
Test for 'creating-financial-models' skill — DCF Valuation Engine
Validates that the Agent created a DCF valuation class for QuantLib
with NPV computation, term-structure discounting, and sensitivity analysis.
"""

import os
import re

import pytest


class TestCreatingFinancialModels:
    """Verify QuantLib DCF valuation engine."""

    REPO_DIR = "/workspace/QuantLib"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_header_exists(self):
        """ql/instruments/dcfvaluation.hpp must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "ql/instruments/dcfvaluation.hpp")
        )

    def test_implementation_exists(self):
        """ql/instruments/dcfvaluation.cpp must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "ql/instruments/dcfvaluation.cpp")
        )

    # ------------------------------------------------------------------
    # L1: C++ structure
    # ------------------------------------------------------------------

    def test_header_has_include_guard(self):
        """Header must have include guard or pragma once."""
        content = self._read("ql/instruments/dcfvaluation.hpp")
        patterns = [r"#ifndef", r"#pragma\s+once"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Header missing include guard"

    def test_header_declares_class(self):
        """Header must declare a DCF valuation class."""
        content = self._read("ql/instruments/dcfvaluation.hpp")
        patterns = [
            r"class\s+\w*[Dd][Cc][Ff]\w*",
            r"class\s+\w*Valuation\w*",
            r"class\s+\w*DCF\w*",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "No DCF valuation class declared"

    def test_implementation_includes_header(self):
        """Implementation must include the header."""
        content = self._read("ql/instruments/dcfvaluation.cpp")
        patterns = [r"#include.*dcfvaluation\.hpp", r"#include.*dcfvaluation\.h"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Implementation does not include header"

    # ------------------------------------------------------------------
    # L2: NPV computation
    # ------------------------------------------------------------------

    def test_computes_npv(self):
        """Class must compute NPV (Net Present Value)."""
        content = self._read("ql/instruments/dcfvaluation.cpp")
        patterns = [
            r"[Nn][Pp][Vv]",
            r"net.*present.*value",
            r"presentValue",
            r"present_value",
            r"NPV\(",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Class does not compute NPV"

    def test_accepts_cash_flows(self):
        """Class must accept a series of cash flows."""
        combined = self._read("ql/instruments/dcfvaluation.hpp") + self._read(
            "ql/instruments/dcfvaluation.cpp"
        )
        patterns = [
            r"[Cc]ash[Ff]low",
            r"cashflow",
            r"vector.*flow",
            r"Leg",
            r"std::vector",
        ]
        assert any(
            re.search(p, combined) for p in patterns
        ), "Class does not accept cash flows"

    def test_supports_discount_rate(self):
        """Class must support flat discount rate."""
        combined = self._read("ql/instruments/dcfvaluation.hpp") + self._read(
            "ql/instruments/dcfvaluation.cpp"
        )
        patterns = [r"discount.*rate", r"rate", r"Rate", r"discountRate"]
        assert any(
            re.search(p, combined, re.IGNORECASE) for p in patterns
        ), "Class does not support discount rate"

    def test_supports_term_structure(self):
        """Class must support term-structure-based discounting."""
        combined = self._read("ql/instruments/dcfvaluation.hpp") + self._read(
            "ql/instruments/dcfvaluation.cpp"
        )
        patterns = [
            r"[Tt]erm[Ss]tructure",
            r"YieldTermStructure",
            r"term_structure",
            r"yield.*curve",
            r"Handle.*YieldTermStructure",
        ]
        assert any(
            re.search(p, combined) for p in patterns
        ), "Class does not support term structure discounting"

    def test_sensitivity_analysis(self):
        """Class must support sensitivity analysis across discount rates."""
        combined = self._read("ql/instruments/dcfvaluation.hpp") + self._read(
            "ql/instruments/dcfvaluation.cpp"
        )
        patterns = [
            r"sensitiv",
            r"scenario",
            r"range.*rate",
            r"for.*rate",
            r"stress",
            r"sweep",
        ]
        assert any(
            re.search(p, combined, re.IGNORECASE) for p in patterns
        ), "Class does not support sensitivity analysis"

    # ------------------------------------------------------------------
    # L2: Terminal value
    # ------------------------------------------------------------------

    def test_terminal_value(self):
        """Class should support terminal value for perpetuity models."""
        combined = self._read("ql/instruments/dcfvaluation.hpp") + self._read(
            "ql/instruments/dcfvaluation.cpp"
        )
        patterns = [r"terminal", r"Terminal", r"perpetuity", r"growth.*rate"]
        assert any(
            re.search(p, combined, re.IGNORECASE) for p in patterns
        ), "Class does not support terminal value"

    # ------------------------------------------------------------------
    # L2: Input validation
    # ------------------------------------------------------------------

    def test_validates_inputs(self):
        """Class must validate inputs (negative rates, empty flows)."""
        content = self._read("ql/instruments/dcfvaluation.cpp")
        patterns = [
            r"throw",
            r"error",
            r"assert",
            r"require",
            r"invalid",
            r"empty",
            r"negative",
        ]
        found = sum(1 for p in patterns if re.search(p, content, re.IGNORECASE))
        assert found >= 2, "Implementation lacks input validation"

    # ------------------------------------------------------------------
    # L2: CMakeLists integration
    # ------------------------------------------------------------------

    def test_cmake_includes_new_files(self):
        """CMakeLists.txt must include the new source file."""
        cmake_path = os.path.join(self.REPO_DIR, "ql/CMakeLists.txt")
        assert os.path.isfile(cmake_path), "ql/CMakeLists.txt not found"
        with open(cmake_path, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(
            r"dcfvaluation", content, re.IGNORECASE
        ), "CMakeLists.txt does not include dcfvaluation"
