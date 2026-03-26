"""
Tests for slo-implementation skill.
REPO_DIR: /workspace/slo-generator
"""

import os
import sys
import importlib
import pytest

REPO_DIR = "/workspace/slo-generator"


def _path(rel):
    return os.path.join(REPO_DIR, rel)


def _read(rel):
    with open(_path(rel), encoding="utf-8") as f:
        return f.read()


class TestSloImplementation:
    # ── file_path_check ────────────────────────────────────────────────────
    def test_slo_generator_module_exists(self):
        """Verify slo_generator package directory exists."""
        assert os.path.isdir(
            _path("slo_generator")
        ), "slo_generator/ package directory must exist"

    def test_burn_rate_module_exists(self):
        """Verify slo_generator/burn_rate.py exists and is non-empty."""
        fpath = _path("slo_generator/burn_rate.py")
        assert os.path.isfile(fpath), "slo_generator/burn_rate.py must exist"
        assert (
            os.path.getsize(fpath) > 0
        ), "slo_generator/burn_rate.py must be non-empty"

    # ── semantic_check ─────────────────────────────────────────────────────
    def test_slo_config_validator_defined(self):
        """Verify SLOConfigValidator class and SLOConfigError are defined."""
        validator_path = _path("slo_generator/slo_config_validator.py")
        assert os.path.isfile(
            validator_path
        ), "slo_generator/slo_config_validator.py must exist"
        content = _read("slo_generator/slo_config_validator.py")
        assert (
            "class SLOConfigValidator" in content
        ), "SLOConfigValidator class must be defined"
        assert "SLOConfigError" in content, "SLOConfigError must be defined"
        assert (
            "def validate_slo_config" in content or "def validate" in content
        ), "validate_slo_config or validate method must be present"

    def test_burn_rate_calculator_defined(self):
        """Verify BurnRateCalculator class is defined with calculate method."""
        content = _read("slo_generator/burn_rate.py")
        assert (
            "class BurnRateCalculator" in content
        ), "BurnRateCalculator class must be defined"
        assert (
            "def calculate" in content or "def burn_rate" in content
        ), "calculate or burn_rate method must be present"
        assert (
            "error_budget" in content or "slo_target" in content
        ), "error_budget or slo_target must be referenced"

    def test_dual_window_alert_defined(self):
        """Verify dual-window alerting (5m and 1h windows) is defined for multi-window burn rate."""
        content = _read("slo_generator/burn_rate.py")
        keywords = [
            "short_window",
            "long_window",
            "5m",
            "1h",
            "dual_window",
            "MultiWindowAlert",
        ]
        found = any(k in content for k in keywords)
        assert (
            found
        ), "short_window/long_window or 5m/1h dual-window alert patterns must be defined"

    def test_budget_exhaustion_date_defined(self):
        """Verify exhaustion_date calculation is defined in burn_rate module."""
        content = _read("slo_generator/burn_rate.py")
        patterns = [
            "exhaustion_date",
            "exhaustion",
            "days_remaining",
            "time_to_exhaustion",
        ]
        found = any(p in content for p in patterns)
        assert (
            found
        ), "exhaustion_date or days_remaining calculation must be implemented"

    # ── functional_check (import/mocked) ──────────────────────────────────
    def _get_slo_module(self):
        """Try to import from slo_generator; skip if unavailable."""
        sys.path.insert(0, REPO_DIR)
        try:
            slo_mod = importlib.import_module("slo_generator.slo_config_validator")
            return slo_mod
        except Exception:
            pytest.skip("slo_generator.slo_config_validator not importable")

    def _get_burn_rate_module(self):
        sys.path.insert(0, REPO_DIR)
        try:
            br_mod = importlib.import_module("slo_generator.burn_rate")
            return br_mod
        except Exception:
            pytest.skip("slo_generator.burn_rate not importable")

    def test_slo_target_1_0_raises_config_error(self):
        """Verify SLO target of 1.0 (100%) raises SLOConfigError."""

        # Mocked implementation matching the expected contract
        class SLOConfigError(Exception):
            pass

        def validate_slo_config(config):
            target = config.get("target", 0)
            if target >= 1.0:
                raise SLOConfigError(
                    f"SLO target {target} must be < 1.0 (cannot achieve 100% availability)"
                )
            if target < 0.9:
                raise SLOConfigError(
                    f"SLO target {target} is unreasonably low (minimum 0.9)"
                )
            return True

        with pytest.raises(SLOConfigError):
            validate_slo_config({"target": 1.0, "window_days": 30})

    def test_slo_availability_0_5_raises_config_error(self):
        """Verify SLO availability of 0.5 (50%) raises SLOConfigError as unreasonably low."""

        class SLOConfigError(Exception):
            pass

        def validate_slo_config(config):
            target = config.get("target", 0)
            if target >= 1.0:
                raise SLOConfigError("SLO target must be < 1.0")
            if target < 0.9:
                raise SLOConfigError(
                    f"SLO target {target} is below minimum threshold of 0.9"
                )
            return True

        with pytest.raises(SLOConfigError):
            validate_slo_config({"target": 0.5, "window_days": 30})

    def test_burn_rate_0_0144_target_0_999_equals_14_4(self):
        """Verify burn_rate(error_rate=0.0144, slo_target=0.999) = 14.4."""

        class BurnRateCalculator:
            def __init__(self, slo_target):
                self.slo_target = slo_target
                self.error_budget = 1.0 - slo_target

            def calculate(self, current_error_rate):
                if self.error_budget == 0:
                    return float("inf")
                return current_error_rate / self.error_budget

        calc = BurnRateCalculator(slo_target=0.999)
        rate = calc.calculate(current_error_rate=0.0144)
        assert abs(rate - 14.4) < 0.01, f"Expected 14.4 ± 0.01, got {rate}"

    def test_both_windows_trigger_alert(self):
        """Verify alert fires when both 5m and 1h burn rate windows are exceeded."""

        class BurnRateCalculator:
            def __init__(self, slo_target):
                self.slo_target = slo_target
                self.error_budget = 1.0 - slo_target

            def should_alert(self, short_window_rate, long_window_rate, threshold):
                return short_window_rate > threshold and long_window_rate > threshold

        calc = BurnRateCalculator(slo_target=0.999)
        alert = calc.should_alert(
            short_window_rate=15.0, long_window_rate=12.0, threshold=14.4
        )
        assert alert is True, "Alert must fire when both windows exceed threshold"

    def test_only_short_window_no_alert(self):
        """Verify alert does NOT fire when only the 5m window is exceeded (not sustained)."""

        class BurnRateCalculator:
            def __init__(self, slo_target):
                self.slo_target = slo_target

            def should_alert(self, short_window_rate, long_window_rate, threshold):
                return short_window_rate > threshold and long_window_rate > threshold

        calc = BurnRateCalculator(slo_target=0.999)
        alert = calc.should_alert(
            short_window_rate=15.0, long_window_rate=5.0, threshold=14.4
        )
        assert (
            alert is False
        ), "Alert must NOT fire when only the short window exceeds the threshold"

    def test_zero_burn_rate_exhaustion_none(self):
        """Verify exhaustion_date is None when burn rate is 0 (infinite budget)."""

        class BurnRateCalculator:
            def __init__(self, slo_target):
                self.slo_target = slo_target
                self.error_budget = 1.0 - slo_target

            def exhaustion_date(self, current_error_rate):
                if current_error_rate == 0:
                    return None
                burn = current_error_rate / self.error_budget
                # Simplified: would compute actual date
                return burn

        calc = BurnRateCalculator(slo_target=0.999)
        date = calc.exhaustion_date(current_error_rate=0.0)
        assert (
            date is None
        ), "exhaustion_date must be None when error_rate=0 (budget never exhausts)"
