"""
Test for 'tdd-workflow' skill — Smart Coupon Calculator
Validates that the Agent implemented SmartCouponCalculator with progressive,
category, and user-tier discounts in src/calculator.py.
"""

import os
import sys
import importlib
import subprocess
import pytest


class TestTddWorkflow:
    """Verify SmartCouponCalculator implementation correctness."""

    REPO_DIR = "/workspace/python"

    @classmethod
    def setup_class(cls):
        """Add repo to sys.path so we can import src.calculator."""
        if cls.REPO_DIR not in sys.path:
            sys.path.insert(0, cls.REPO_DIR)

    # ------------------------------------------------------------------
    # L1: file & syntax checks
    # ------------------------------------------------------------------

    def test_calculator_file_exists(self):
        """src/calculator.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "src", "calculator.py")
        assert os.path.isfile(fpath), "src/calculator.py is missing"

    def test_calculator_compiles(self):
        """src/calculator.py must compile without syntax errors."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "src/calculator.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: functional verification — import & instantiate
    # ------------------------------------------------------------------

    def _get_calculator(self):
        """Helper: import and return a fresh SmartCouponCalculator instance."""
        mod = importlib.import_module("src.calculator")
        importlib.reload(mod)
        cls = getattr(mod, "SmartCouponCalculator", None)
        assert (
            cls is not None
        ), "SmartCouponCalculator class not found in src/calculator.py"
        return cls()

    def test_class_exists(self):
        """SmartCouponCalculator class must be importable."""
        calc = self._get_calculator()
        assert calc is not None

    # --- Progressive Discount ---

    def test_progressive_no_discount_below_100(self):
        """Order < $100 should get no progressive discount."""
        calc = self._get_calculator()
        items = [{"name": "A", "price": 50, "quantity": 1}]
        result = calc.calculate(items=items, user_tier="regular")
        # Exact price depends on implementation; no progressive discount
        assert isinstance(result, (int, float)), "calculate() must return a number"
        assert result == pytest.approx(50, abs=0.01), f"Expected 50, got {result}"

    def test_progressive_10_off_at_100(self):
        """Order = $100 should get $10 off progressive discount."""
        calc = self._get_calculator()
        items = [{"name": "A", "price": 100, "quantity": 1}]
        result = calc.calculate(items=items, user_tier="regular")
        assert result == pytest.approx(90, abs=0.01), f"Expected 90, got {result}"

    def test_progressive_25_off_at_200(self):
        """Order = $200 should get $25 off progressive discount."""
        calc = self._get_calculator()
        items = [{"name": "A", "price": 200, "quantity": 1}]
        result = calc.calculate(items=items, user_tier="regular")
        assert result == pytest.approx(175, abs=0.01), f"Expected 175, got {result}"

    # --- Category Discount ---

    def test_category_discount_10_percent(self):
        """Items in promotional categories should get 10% off."""
        calc = self._get_calculator()
        items = [
            {
                "name": "Promo item",
                "price": 80,
                "quantity": 1,
                "category": "electronics",
            }
        ]
        result = calc.calculate(
            items=items,
            user_tier="regular",
            promo_categories=["electronics"],
        )
        # 80 * 0.9 = 72, below 100 so no progressive
        assert result == pytest.approx(72, abs=0.01), f"Expected 72, got {result}"

    def test_category_discount_only_promo(self):
        """Non-promo category items should not get category discount."""
        calc = self._get_calculator()
        items = [
            {"name": "Promo", "price": 50, "quantity": 1, "category": "electronics"},
            {"name": "Normal", "price": 50, "quantity": 1, "category": "food"},
        ]
        result = calc.calculate(
            items=items,
            user_tier="regular",
            promo_categories=["electronics"],
        )
        # electronics: 50*0.9=45, food: 50, total 95 < 100 no progressive
        assert result == pytest.approx(95, abs=0.5), f"Expected ~95, got {result}"

    # --- User Tier Discount ---

    def test_vip_5_percent_off(self):
        """VIP members get 5% off final price."""
        calc = self._get_calculator()
        items = [{"name": "A", "price": 50, "quantity": 1}]
        result = calc.calculate(items=items, user_tier="VIP")
        assert result == pytest.approx(47.5, abs=0.01), f"Expected 47.5, got {result}"

    def test_svip_10_percent_off(self):
        """SVIP members get 10% off final price."""
        calc = self._get_calculator()
        items = [{"name": "A", "price": 50, "quantity": 1}]
        result = calc.calculate(items=items, user_tier="SVIP")
        assert result == pytest.approx(45, abs=0.01), f"Expected 45, got {result}"

    # --- Stacking ---

    def test_all_discounts_stacked(self):
        """Progressive + category + SVIP should stack optimally."""
        calc = self._get_calculator()
        items = [
            {"name": "Gadget", "price": 120, "quantity": 1, "category": "electronics"},
            {"name": "Book", "price": 100, "quantity": 1, "category": "books"},
        ]
        result = calc.calculate(
            items=items,
            user_tier="SVIP",
            promo_categories=["electronics"],
        )
        # electronics: 120*0.9=108, books: 100, subtotal=208
        # Progressive: 208 >= 200 → -25 → 183
        # SVIP: 183*0.9 = 164.7
        assert isinstance(result, (int, float))
        assert 140 <= result <= 190, f"Stacked discount result {result} looks wrong"

    # --- Edge Cases ---

    def test_zero_amount(self):
        """Zero-priced items should not cause errors."""
        calc = self._get_calculator()
        items = [{"name": "Free", "price": 0, "quantity": 1}]
        result = calc.calculate(items=items, user_tier="regular")
        assert result == pytest.approx(0, abs=0.01)

    def test_empty_cart(self):
        """Empty shopping cart should return 0."""
        calc = self._get_calculator()
        result = calc.calculate(items=[], user_tier="regular")
        assert result == pytest.approx(0, abs=0.01)

    def test_invalid_tier_handled(self):
        """Invalid user tier should fallback to regular pricing or raise ValueError."""
        calc = self._get_calculator()
        items = [{"name": "A", "price": 50, "quantity": 1}]
        try:
            result = calc.calculate(items=items, user_tier="UNKNOWN")
            # If no error, should be treated as regular (no tier discount)
            assert result == pytest.approx(50, abs=0.01)
        except (ValueError, KeyError):
            pass  # Acceptable to raise on invalid tier
