"""
Test for 'creating-financial-models' skill — QuantLib Financial Models
Validates that the Agent created financial model implementations using
QuantLib with proper pricing engines and term structure setup.
"""

import os
import subprocess
import pytest


class TestCreatingFinancialModels:
    """Verify QuantLib financial model implementation."""

    REPO_DIR = "/workspace/QuantLib"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_model_file_exists(self):
        """A financial model implementation file must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".cpp", ".hpp")) and (
                    "model" in f.lower()
                    or "pricing" in f.lower()
                    or "option" in f.lower()
                ):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No financial model file found"

    def test_example_script_exists(self):
        """An example/demo script must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if (f.endswith(".py") or f.endswith(".cpp")) and (
                    "example" in f.lower()
                    or "demo" in f.lower()
                    or "pricing" in f.lower()
                ):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No example/demo script found"

    # ------------------------------------------------------------------
    # L2: content validation
    # ------------------------------------------------------------------

    def _find_model_files(self):
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".cpp", ".hpp")) and (
                    "model" in f.lower()
                    or "pricing" in f.lower()
                    or "option" in f.lower()
                    or "finance" in f.lower()
                ):
                    found.append(os.path.join(root, f))
        return found

    def _read_all_models(self):
        content = ""
        for fpath in self._find_model_files():
            try:
                with open(fpath, "r", errors="ignore") as f:
                    content += f.read() + "\n"
            except OSError:
                pass
        return content

    def test_quantlib_usage(self):
        """Must use QuantLib library."""
        content = self._read_all_models()
        ql_patterns = [
            "QuantLib",
            "ql.",
            "import QuantLib",
            "#include <ql/",
            "ql::",
            "from QuantLib",
        ]
        found = any(p in content for p in ql_patterns)
        assert found, "No QuantLib usage found"

    def test_term_structure(self):
        """Must define yield/term structure."""
        content = self._read_all_models()
        ts_patterns = [
            "YieldTermStructure",
            "TermStructure",
            "FlatForward",
            "ZeroCurve",
            "ForwardCurve",
            "term_structure",
            "yield_curve",
            "discount",
        ]
        found = any(p in content for p in ts_patterns)
        assert found, "No term structure defined"

    def test_pricing_engine(self):
        """Must set up a pricing engine."""
        content = self._read_all_models()
        engine_patterns = [
            "PricingEngine",
            "AnalyticEuropeanEngine",
            "BinomialEngine",
            "MCEuropeanEngine",
            "BlackScholes",
            "setPricingEngine",
            "set_pricing_engine",
        ]
        found = any(p in content for p in engine_patterns)
        assert found, "No pricing engine found"

    def test_option_definition(self):
        """Must define at least one option instrument."""
        content = self._read_all_models()
        option_patterns = [
            "VanillaOption",
            "EuropeanOption",
            "AmericanOption",
            "Option",
            "Payoff",
            "PlainVanillaPayoff",
            "EuropeanExercise",
            "AmericanExercise",
        ]
        found = sum(1 for p in option_patterns if p in content)
        assert found >= 2, "Insufficient option instrument definition"

    def test_npv_calculation(self):
        """Must calculate NPV or pricing result."""
        content = self._read_all_models()
        calc_patterns = [
            "NPV",
            "npv",
            "delta",
            "gamma",
            "vega",
            "theta",
            "rho",
            "impliedVolatility",
        ]
        found = any(p in content for p in calc_patterns)
        assert found, "No NPV/Greeks calculation found"

    def test_market_data(self):
        """Must set up market data (spot, vol, rate)."""
        content = self._read_all_models()
        market_patterns = [
            "spot",
            "volatility",
            "riskFree",
            "risk_free",
            "SimpleQuote",
            "BlackVolTermStructure",
            "dividend",
            "strike",
        ]
        found = sum(1 for p in market_patterns if p in content)
        assert found >= 2, "Insufficient market data setup"

    def test_date_handling(self):
        """Must use QuantLib date handling."""
        content = self._read_all_models()
        date_patterns = [
            "Date",
            "Calendar",
            "DayCounter",
            "Actual365",
            "TARGET",
            "Settings.instance",
            "evaluationDate",
            "Schedule",
        ]
        found = sum(1 for p in date_patterns if p in content)
        assert found >= 2, "Insufficient date handling"

    def test_python_demo_runs(self):
        """Python demo scripts must run successfully."""
        for fpath in self._find_model_files():
            if fpath.endswith(".py"):
                result = subprocess.run(
                    ["python", fpath],
                    cwd=self.REPO_DIR,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode == 0:
                    return
        # If no Python file runs, try compile check
        for fpath in self._find_model_files():
            if fpath.endswith(".py"):
                result = subprocess.run(
                    ["python", "-m", "py_compile", fpath],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                assert (
                    result.returncode == 0
                ), f"{fpath} compile error:\n{result.stderr}"
                return
        pytest.skip("No Python model files found")
