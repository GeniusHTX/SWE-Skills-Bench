"""
Test for 'slo-implementation' skill — SLO Implementation Framework
Validates that the Agent implemented SLO calculator, error budget tracker,
and burn rate alerter with YAML-driven configuration.
"""

import os
import re
import sys

import pytest


class TestSloImplementation:
    """Verify SLO implementation framework."""

    REPO_DIR = "/workspace/slo-generator"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_slo_yaml_configs_exist(self):
        """Verify at least one YAML SLO config directory exists."""
        candidates = ("slos/", "config/slos/")
        found = any(
            os.path.isdir(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    def test_slo_calculator_module_exists(self):
        """Verify slo/calculator.py or slo_calculator.py exists."""
        candidates = ("slo/calculator.py", "slo_calculator.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    def test_error_budget_tracker_module_exists(self):
        """Verify slo/budget.py or error_budget_tracker.py exists."""
        candidates = ("slo/budget.py", "error_budget_tracker.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    def test_burn_rate_alerter_module_exists(self):
        """Verify slo/alerter.py or burn_rate_alerter.py exists."""
        candidates = ("slo/alerter.py", "burn_rate_alerter.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    # ── semantic_check ──────────────────────────────────────────────

    def _find_file(self, *candidates):
        for c in candidates:
            p = os.path.join(self.REPO_DIR, c)
            if os.path.isfile(p):
                return p
        return None

    def _read_yaml_dir(self):
        """Read all YAML content from slos/ or config/slos/."""
        for d in ("slos", "config/slos"):
            dirpath = os.path.join(self.REPO_DIR, d)
            if os.path.isdir(dirpath):
                content = ""
                for f in os.listdir(dirpath):
                    if f.endswith((".yaml", ".yml")):
                        content += self._read(os.path.join(dirpath, f))
                return content
        return ""

    def test_yaml_required_fields(self):
        """Verify SLO YAML files contain slo_name, target, window, and sli_query."""
        content = self._read_yaml_dir()
        assert content, "No YAML SLO config files found"
        for kw in ("slo_name", "target", "window", "sli_query"):
            assert kw in content, f"'{kw}' not found in SLO YAML configs"

    def test_slo_calculator_compute_signature(self):
        """Verify SLOCalculator.compute() method is defined."""
        path = self._find_file("slo/calculator.py", "slo_calculator.py")
        assert path, "Calculator module not found"
        content = self._read(path)
        assert "def compute" in content, "compute() method not found"

    def test_is_breached_method_exists(self):
        """Verify ErrorBudgetTracker.is_breached() method is defined."""
        path = self._find_file("slo/budget.py", "error_budget_tracker.py")
        assert path, "Budget tracker module not found"
        content = self._read(path)
        assert "def is_breached" in content, "is_breached() method not found"

    def test_burn_rate_14_4_threshold_defined(self):
        """Verify 14.4 burn rate threshold is referenced in alerter module."""
        path = self._find_file("slo/alerter.py", "burn_rate_alerter.py")
        assert path, "Alerter module not found"
        content = self._read(path)
        assert "14.4" in content, "14.4 threshold not found in alerter"

    # ── functional_check (import) ───────────────────────────────────

    def _skip_unless_importable(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if self.REPO_DIR not in sys.path:
            sys.path.insert(0, self.REPO_DIR)

    def test_error_budget_formula_999_target(self):
        """SLOCalculator: target=0.999, window_minutes=43200 -> error_budget_minutes~43.2."""
        self._skip_unless_importable()
        try:
            from slo.calculator import SLOCalculator
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        result = SLOCalculator().compute(
            sli_values=[], target=0.999, window_minutes=43200)
        assert abs(result["error_budget_minutes"] - 43.2) < 0.1, \
            f"error_budget_minutes={result['error_budget_minutes']}, expected ~43.2"

    def test_burn_rate_above_threshold_alerts(self):
        """BurnRateAlerter.check(burn_rate=15.0, threshold=14.4) returns True."""
        self._skip_unless_importable()
        try:
            from slo.alerter import BurnRateAlerter
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        result = BurnRateAlerter().check(current_burn_rate=15.0, threshold=14.4)
        assert result is True, "Burn rate above threshold must return True"

    def test_burn_rate_below_threshold_no_alert(self):
        """BurnRateAlerter.check(burn_rate=5.0, threshold=14.4) returns False."""
        self._skip_unless_importable()
        try:
            from slo.alerter import BurnRateAlerter
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        result = BurnRateAlerter().check(current_burn_rate=5.0, threshold=14.4)
        assert result is False, "Burn rate below threshold must return False"
