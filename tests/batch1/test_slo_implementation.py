"""
Test for 'slo-implementation' skill — SLO Implementation Framework
Validates that the Agent implemented PrometheusAvailabilitySLI and
slo_config_validator in the slo-generator project.
"""

import os
import sys
import subprocess
import pytest


class TestSloImplementation:
    """Verify SLO implementation modules in slo-generator."""

    REPO_DIR = "/workspace/slo-generator"

    @classmethod
    def setup_class(cls):
        if cls.REPO_DIR not in sys.path:
            sys.path.insert(0, cls.REPO_DIR)

    # ------------------------------------------------------------------
    # L1: file existence & syntax
    # ------------------------------------------------------------------

    def test_prometheus_availability_exists(self):
        """slo_generator/backends/prometheus_availability.py must exist."""
        fpath = os.path.join(
            self.REPO_DIR, "slo_generator", "backends", "prometheus_availability.py"
        )
        assert os.path.isfile(fpath), "prometheus_availability.py not found"

    def test_config_validator_exists(self):
        """slo_generator/utils/slo_config_validator.py must exist."""
        fpath = os.path.join(
            self.REPO_DIR, "slo_generator", "utils", "slo_config_validator.py"
        )
        assert os.path.isfile(fpath), "slo_config_validator.py not found"

    def test_prometheus_availability_compiles(self):
        """prometheus_availability.py must compile."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "py_compile",
                "slo_generator/backends/prometheus_availability.py",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_config_validator_compiles(self):
        """slo_config_validator.py must compile."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "py_compile",
                "slo_generator/utils/slo_config_validator.py",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: structural verification
    # ------------------------------------------------------------------

    def _read_prom(self):
        fpath = os.path.join(
            self.REPO_DIR, "slo_generator", "backends", "prometheus_availability.py"
        )
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()

    def _read_validator(self):
        fpath = os.path.join(
            self.REPO_DIR, "slo_generator", "utils", "slo_config_validator.py"
        )
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()

    def test_prometheus_sli_class_defined(self):
        """PrometheusAvailabilitySLI class must exist."""
        source = self._read_prom()
        assert (
            "PrometheusAvailabilitySLI" in source
        ), "PrometheusAvailabilitySLI class not found"

    def test_compute_sli_method(self):
        """compute_sli method must be defined."""
        source = self._read_prom()
        assert "compute_sli" in source, "compute_sli method not found"

    def test_evaluate_slo_method(self):
        """evaluate_slo method must be defined."""
        source = self._read_prom()
        assert "evaluate_slo" in source, "evaluate_slo method not found"

    def test_slo_goal_configurable(self):
        """SLO target/goal should be configurable (e.g. 0.999)."""
        source = self._read_prom()
        goal_patterns = ["goal", "target", "objective", "slo"]
        found = sum(1 for p in goal_patterns if p in source.lower())
        assert found >= 1, "No SLO goal/target configuration found"

    def test_validate_slo_config_function(self):
        """validate_slo_config function must be defined in validator."""
        source = self._read_validator()
        assert "validate_slo_config" in source, "validate_slo_config function not found"

    def test_validator_checks_required_fields(self):
        """Validator must check required fields."""
        source = self._read_validator()
        required = ["service_name", "slo_name", "backend", "goal", "window"]
        found = sum(1 for f in required if f in source)
        assert found >= 4, f"Validator only checks {found}/5 required fields"

    def test_validator_raises_value_error(self):
        """Validator should raise ValueError on invalid config."""
        source = self._read_validator()
        assert "ValueError" in source, "ValueError not raised in validator"

    def test_validator_checks_goal_range(self):
        """Validator must ensure goal is in (0, 1) range."""
        source = self._read_validator()
        range_patterns = ["0", "1", "goal", "range", "<", ">"]
        found = sum(1 for p in range_patterns if p in source)
        assert found >= 3, "Goal range validation not clearly implemented"

    def test_import_prometheus_availability(self):
        """PrometheusAvailabilitySLI should be importable."""
        result = subprocess.run(
            [
                "python",
                "-c",
                "import sys; sys.path.insert(0,'.'); "
                "from slo_generator.backends.prometheus_availability import "
                "PrometheusAvailabilitySLI; print('OK')",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Import failed:\n{result.stderr}"

    def test_import_validate_slo_config(self):
        """validate_slo_config should be importable."""
        result = subprocess.run(
            [
                "python",
                "-c",
                "import sys; sys.path.insert(0,'.'); "
                "from slo_generator.utils.slo_config_validator import "
                "validate_slo_config; print('OK')",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Import failed:\n{result.stderr}"
