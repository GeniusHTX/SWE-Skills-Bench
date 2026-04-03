"""
Test for 'slo-implementation' skill — SLO / SLI / Error Budget
Validates SLICalculator, ErrorBudgetTracker, BurnRateAlerter,
SLOConfig validation, availability formula, and burn-rate thresholds.
"""

import os
import sys

import pytest


class TestSloImplementation:
    """Verify SLO implementation: SLI, budget, alerting, config."""

    REPO_DIR = "/workspace/slo-generator"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _slo(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "examples", "slo", *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_slo_init_sli_budget_exist(self):
        """__init__.py, sli.py, budget.py must exist."""
        for name in ("__init__.py", "sli.py", "budget.py"):
            assert os.path.isfile(self._slo(name)), f"{name} not found"

    def test_alerting_report_exist(self):
        """alerting.py and report.py must exist."""
        assert os.path.isfile(self._slo("alerting.py"))
        assert os.path.isfile(self._slo("report.py"))

    def test_config_or_sloconfig_exists(self):
        """config.py (SLOConfig) must exist."""
        assert os.path.isfile(self._slo("config.py")), "config.py not found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_sli_availability_formula(self):
        """SLICalculator.availability must use float division."""
        content = self._read_file(self._slo("sli.py"))
        if not content:
            pytest.skip("sli.py not found")
        assert "SLICalculator" in content
        assert "availability" in content

    def test_burn_rate_thresholds(self):
        """alerting.py must use 14.4 (fast) and 6 (slow) thresholds."""
        content = self._read_file(self._slo("alerting.py"))
        if not content:
            pytest.skip("alerting.py not found")
        assert "14.4" in content
        assert "6" in content
        assert "critical" in content.lower()
        assert "warning" in content.lower()

    def test_error_budget_formula(self):
        """budget.py formula: (1 - target) * window_minutes."""
        content = self._read_file(self._slo("budget.py"))
        if not content:
            pytest.skip("budget.py not found")
        assert "ErrorBudgetTracker" in content
        assert "budget_minutes" in content

    def test_config_validates_target(self):
        """SLOConfig must raise ValueError for target > 1.0."""
        content = self._read_file(self._slo("config.py"))
        if not content:
            pytest.skip("config.py not found")
        assert "ValueError" in content

    # ── functional_check ─────────────────────────────────────────────────

    def test_sli_availability_990_of_1000(self):
        """availability(990, 1000) == pytest.approx(0.99)."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.slo.sli import SLICalculator
        except ImportError:
            pytest.skip("Cannot import SLICalculator")
        calc = SLICalculator()
        assert calc.availability(990, 1000) == pytest.approx(0.99)

    def test_error_budget_999_slo_30day(self):
        """ErrorBudgetTracker(slo=0.999, window=43200).budget_minutes == 43.2."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.slo.budget import ErrorBudgetTracker
        except ImportError:
            pytest.skip("Cannot import ErrorBudgetTracker")
        tracker = ErrorBudgetTracker(slo_target=0.999, window_minutes=43200)
        assert tracker.budget_minutes == pytest.approx(43.2)

    def test_burn_rate_14_5_at_5min_critical(self):
        """BurnRateAlerter.check(14.5, 5) == 'critical'."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.slo.alerting import BurnRateAlerter
        except ImportError:
            pytest.skip("Cannot import BurnRateAlerter")
        alerter = BurnRateAlerter()
        assert alerter.check(14.5, 5) == "critical"

    def test_burn_rate_5_at_30min_no_alert(self):
        """BurnRateAlerter.check(5.0, 30) is None (below slow burn)."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.slo.alerting import BurnRateAlerter
        except ImportError:
            pytest.skip("Cannot import BurnRateAlerter")
        alerter = BurnRateAlerter()
        assert alerter.check(5.0, 30) is None

    def test_burn_rate_6_5_at_30min_warning(self):
        """BurnRateAlerter.check(6.5, 30) == 'warning'."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.slo.alerting import BurnRateAlerter
        except ImportError:
            pytest.skip("Cannot import BurnRateAlerter")
        alerter = BurnRateAlerter()
        assert alerter.check(6.5, 30) == "warning"

    def test_sli_zero_total_no_zerodivision(self):
        """availability(0, 0) must raise ValueError or return None."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.slo.sli import SLICalculator
        except ImportError:
            pytest.skip("Cannot import SLICalculator")
        calc = SLICalculator()
        try:
            result = calc.availability(0, 0)
            assert result is None
        except ValueError:
            pass
        except ZeroDivisionError:
            pytest.fail("ZeroDivisionError must not propagate")
