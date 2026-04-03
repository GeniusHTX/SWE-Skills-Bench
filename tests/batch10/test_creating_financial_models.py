"""
Test for 'creating-financial-models' skill — QuantLib Financial Models
Validates that the Agent created DCF, Monte Carlo, and sensitivity analysis
models using the QuantLib library.
"""

import os
import re

import pytest


class TestCreatingFinancialModels:
    """Verify QuantLib financial model implementation."""

    REPO_DIR = "/workspace/QuantLib"

    def test_dcf_model_file_exists(self):
        """DCF (Discounted Cash Flow) model file must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".cpp", ".hpp")):
                    if "dcf" in f.lower() or "discount" in f.lower() or "cashflow" in f.lower():
                        found = True
                        break
            if found:
                break
        assert found, "DCF model file not found"

    def test_monte_carlo_model_exists(self):
        """Monte Carlo simulation model must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".cpp", ".hpp")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Mm]onte.?[Cc]arlo|MonteCarlo|monte_carlo", content):
                        found = True
                        break
            if found:
                break
        assert found, "Monte Carlo model not found"

    def test_sensitivity_analysis_exists(self):
        """Sensitivity analysis module must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".cpp", ".hpp")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"sensitiv|greek|delta|gamma|vega", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Sensitivity analysis module not found"

    def test_dcf_uses_discount_factor(self):
        """DCF model must calculate discount factors."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".cpp", ".hpp")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"discount.*factor|present.*value|NPV|npv", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "DCF model does not calculate discount factors"

    def test_monte_carlo_uses_random_paths(self):
        """Monte Carlo model must generate random paths."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".cpp", ".hpp")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"random|normal|GaussianRng|MersenneTwister|simulation", content, re.IGNORECASE):
                        if re.search(r"path|sample|iteration|num_paths", content, re.IGNORECASE):
                            found = True
                            break
            if found:
                break
        assert found, "Monte Carlo does not generate random paths"

    def test_yield_curve_or_term_structure(self):
        """Model must use a yield curve or term structure."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".cpp", ".hpp")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Yy]ield[Cc]urve|[Tt]erm[Ss]tructure|YieldTermStructure|FlatForward", content):
                        found = True
                        break
            if found:
                break
        assert found, "No yield curve or term structure found"

    def test_option_pricing_or_valuation(self):
        """Models should include option pricing or instrument valuation."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".cpp", ".hpp")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Oo]ption|[Vv]aluation|[Pp]ricing|Black.?Scholes|setPricingEngine", content):
                        found = True
                        break
            if found:
                break
        assert found, "No option pricing or valuation found"

    def test_risk_free_rate_defined(self):
        """Models must define or accept a risk-free rate."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".cpp", ".hpp")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"risk.free|riskFree|risk_free_rate|r_f\b", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No risk-free rate parameter found"

    def test_volatility_parameter(self):
        """Models must include volatility as a parameter."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".cpp", ".hpp")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Vv]olatility|sigma|vol\b|BlackVol", content):
                        found = True
                        break
            if found:
                break
        assert found, "No volatility parameter found"

    def test_output_or_result_formatting(self):
        """Models must format and output results."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".cpp", ".hpp")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"print|cout|result|output|format|report", content, re.IGNORECASE):
                        if re.search(r"NPV|price|value|cashflow", content, re.IGNORECASE):
                            found = True
                            break
            if found:
                break
        assert found, "No result formatting or output found"

    def test_date_handling_with_quantlib(self):
        """Models should use QuantLib date handling."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".cpp", ".hpp")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"Date\(|Calendar|Schedule|DayCounter|ActualActual|Thirty360", content):
                        found = True
                        break
            if found:
                break
        assert found, "No QuantLib date handling found"
