"""
Test for 'creating-financial-models' skill — Financial Models (QuantLib-backed)
Validates bond pricer, option pricer (Black-Scholes), yield curve builder,
clean vs dirty price, put-call parity, delta, and input validation.
"""

import math
import os
import subprocess
import sys

import pytest


class TestCreatingFinancialModels:
    """Verify financial model implementations: bonds, options, yield curves."""

    REPO_DIR = "/workspace/QuantLib"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _model(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "examples", "financial_models", *parts)

    def _install_deps(self):
        try:
            import scipy  # noqa: F401
        except ImportError:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "scipy"],
                capture_output=True, timeout=60,
            )

    # ── file_path_check ──────────────────────────────────────────────────

    def test_package_files_exist(self):
        """__init__.py, bond_pricer.py, options.py must exist."""
        for name in ("__init__.py", "bond_pricer.py", "options.py"):
            path = self._model(name)
            assert os.path.isfile(path), f"{path} does not exist"

    def test_yield_curve_and_swap_exist(self):
        """yield_curve.py and swap.py must exist."""
        for name in ("yield_curve.py", "swap.py"):
            path = self._model(name)
            assert os.path.isfile(path), f"{path} does not exist"

    def test_test_file_exists(self):
        """tests/test_financial_models.py must exist."""
        path = os.path.join(self.REPO_DIR, "tests", "test_financial_models.py")
        assert os.path.isfile(path), f"{path} does not exist"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_black_scholes_formula(self):
        """options.py must implement Black-Scholes with d1, d2, norm.cdf."""
        path = self._model("options.py")
        if not os.path.isfile(path):
            pytest.skip("options.py not found")
        content = self._read_file(path)
        assert "d1" in content, "d1 variable not found in Black-Scholes formula"
        assert "d2" in content, "d2 variable not found"
        has_cdf = "norm.cdf" in content or "normalcdf" in content or "NormalDist" in content
        assert has_cdf, "Normal distribution CDF not found"
        assert "exp" in content, "exp() discount factor not found"

    def test_yield_curve_validates_monotonic_dates(self):
        """yield_curve.py must raise ValueError for non-monotonic dates."""
        path = self._model("yield_curve.py")
        if not os.path.isfile(path):
            pytest.skip("yield_curve.py not found")
        content = self._read_file(path)
        assert "ValueError" in content, "ValueError not referenced in yield_curve.py"

    def test_bond_pricer_clean_vs_dirty(self):
        """bond_pricer.py must distinguish clean and dirty price."""
        path = self._model("bond_pricer.py")
        if not os.path.isfile(path):
            pytest.skip("bond_pricer.py not found")
        content = self._read_file(path)
        has_distinction = ("clean" in content.lower() and "dirty" in content.lower()) or "accrued" in content.lower()
        assert has_distinction, "No clean/dirty price distinction in bond_pricer.py"

    def test_option_pricer_validates_negative_vol(self):
        """options.py must raise ValueError for negative sigma."""
        path = self._model("options.py")
        if not os.path.isfile(path):
            pytest.skip("options.py not found")
        content = self._read_file(path)
        assert "ValueError" in content, "ValueError not found for sigma validation"
        has_check = "sigma" in content and ("<= 0" in content or "< 0" in content or "negative" in content.lower())
        assert has_check, "No sigma negativity check found"

    # ── functional_check ─────────────────────────────────────────────────

    def test_zero_coupon_bond_price(self):
        """Zero-coupon bond at 5% rate for 1y = 100/1.05 ≈ 95.238."""
        self._install_deps()
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.financial_models.bond_pricer import BondPricer
        except ImportError:
            pytest.skip("Cannot import BondPricer")
        pricer = BondPricer()
        price = pricer.zero_coupon_price(face_value=100, rate=0.05, time_years=1)
        assert abs(price - 95.238) < 0.1, f"Expected ~95.238, got {price}"

    def test_put_call_parity(self):
        """Call - Put = S - K*exp(-rT) must hold within 0.1 tolerance."""
        self._install_deps()
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.financial_models.options import OptionPricer
        except ImportError:
            pytest.skip("Cannot import OptionPricer")
        pricer = OptionPricer()
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
        call = pricer.price(S=S, K=K, T=T, r=r, sigma=sigma, option_type="call")
        put = pricer.price(S=S, K=K, T=T, r=r, sigma=sigma, option_type="put")
        parity = (call - put) - (S - K * math.exp(-r * T))
        assert abs(parity) < 0.1, f"Put-call parity violated: {parity}"

    def test_deep_itm_call_delta(self):
        """Deep ITM call (S=200, K=100) delta must be > 0.99."""
        self._install_deps()
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.financial_models.options import OptionPricer
        except ImportError:
            pytest.skip("Cannot import OptionPricer")
        pricer = OptionPricer()
        delta = pricer.delta(S=200, K=100, T=1, r=0.05, sigma=0.2, option_type="call")
        assert delta > 0.99, f"Deep ITM call delta should be >0.99, got {delta}"

    def test_yield_curve_non_monotonic_raises(self):
        """Non-monotonic dates must raise ValueError."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.financial_models.yield_curve import YieldCurveBuilder
        except ImportError:
            pytest.skip("Cannot import YieldCurveBuilder")
        with pytest.raises(ValueError):
            YieldCurveBuilder().build(
                dates=["2024-01-01", "2026-01-01", "2025-01-01"],
                rates=[0.03, 0.04, 0.035],
            )

    def test_negative_volatility_raises(self):
        """Negative sigma must raise ValueError."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.financial_models.options import OptionPricer
        except ImportError:
            pytest.skip("Cannot import OptionPricer")
        with pytest.raises(ValueError):
            OptionPricer().price(S=100, K=100, T=1, r=0.05, sigma=-0.2, option_type="call")
