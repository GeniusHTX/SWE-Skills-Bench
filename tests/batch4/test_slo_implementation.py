"""
Test for 'slo-implementation' skill — SLO Implementation
Validates AvailabilitySLI, LatencySLI, and SLO classes for computing
service level indicators and objectives in the slo-generator repo.
"""

import os
import sys
import pytest


class TestSloImplementation:
    """Tests for SLO implementation in the slo-generator repo."""

    REPO_DIR = "/workspace/slo-generator"

    def _read(self, relpath):
        full = os.path.join(self.REPO_DIR, relpath)
        with open(full, "r", errors="ignore") as f:
            return f.read()

    # --- File Path Checks ---

    def test_sli_py_exists(self):
        """Verifies that slo_generator/sli.py exists."""
        path = os.path.join(self.REPO_DIR, "slo_generator", "sli.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_slo_py_exists(self):
        """Verifies that slo_generator/slo.py exists."""
        path = os.path.join(self.REPO_DIR, "slo_generator", "slo.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_init_py_exists(self):
        """Verifies that slo_generator/__init__.py exists."""
        path = os.path.join(self.REPO_DIR, "slo_generator", "__init__.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    # --- Semantic Checks ---

    def test_sem_import_sli(self):
        """AvailabilitySLI and LatencySLI are importable."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from slo_generator.sli import AvailabilitySLI, LatencySLI

            assert AvailabilitySLI is not None
            assert LatencySLI is not None
        finally:
            sys.path[:] = old_path

    def test_sem_import_slo(self):
        """SLO is importable."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from slo_generator.slo import SLO

            assert SLO is not None
        finally:
            sys.path[:] = old_path

    def test_sem_slo_has_methods(self):
        """SLO has is_compliant, error_budget_remaining, burn_rate methods."""
        src = self._read("slo_generator/slo.py")
        assert "def is_compliant" in src, "Missing is_compliant method"
        assert (
            "def error_budget_remaining" in src or "error_budget" in src
        ), "Missing error_budget method"

    def test_sem_sli_has_calculate(self):
        """AvailabilitySLI and LatencySLI have calculate() methods."""
        src = self._read("slo_generator/sli.py")
        assert "def calculate" in src, "Missing calculate method in SLI"

    # --- Functional Checks ---

    def test_func_availability_sli_99_of_100(self):
        """AvailabilitySLI().calculate(99, 100) == approx(0.99)."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from slo_generator.sli import AvailabilitySLI

            result = AvailabilitySLI().calculate(99, 100)
            assert result == pytest.approx(0.99)
        finally:
            sys.path[:] = old_path

    def test_func_availability_sli_100_of_100(self):
        """AvailabilitySLI().calculate(100, 100) == approx(1.0)."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from slo_generator.sli import AvailabilitySLI

            result = AvailabilitySLI().calculate(100, 100)
            assert result == pytest.approx(1.0)
        finally:
            sys.path[:] = old_path

    def test_func_availability_sli_0_of_100(self):
        """AvailabilitySLI().calculate(0, 100) == approx(0.0)."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from slo_generator.sli import AvailabilitySLI

            result = AvailabilitySLI().calculate(0, 100)
            assert result == pytest.approx(0.0)
        finally:
            sys.path[:] = old_path

    def test_func_latency_sli_threshold_100(self):
        """LatencySLI().calculate([50, 100, 150, 200], 100) == approx(0.25)."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from slo_generator.sli import LatencySLI

            result = LatencySLI().calculate([50, 100, 150, 200], 100)
            assert result == pytest.approx(0.25)
        finally:
            sys.path[:] = old_path

    def test_func_latency_sli_all_under_threshold(self):
        """LatencySLI().calculate([50, 80, 90], 100) == approx(1.0)."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from slo_generator.sli import LatencySLI

            result = LatencySLI().calculate([50, 80, 90], 100)
            assert result == pytest.approx(1.0)
        finally:
            sys.path[:] = old_path

    def test_func_slo_creation(self):
        """SLO('test', 0.99, AvailabilitySLI(), 30) creates successfully."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from slo_generator.sli import AvailabilitySLI
            from slo_generator.slo import SLO

            slo = SLO("test", 0.99, AvailabilitySLI(), 30)
            assert slo is not None
        finally:
            sys.path[:] = old_path

    def test_func_slo_is_compliant_true(self):
        """slo.is_compliant(0.995) == True (above 0.99 target)."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from slo_generator.sli import AvailabilitySLI
            from slo_generator.slo import SLO

            slo = SLO("test", 0.99, AvailabilitySLI(), 30)
            assert slo.is_compliant(0.995) is True
        finally:
            sys.path[:] = old_path

    def test_func_slo_is_compliant_false(self):
        """slo.is_compliant(0.989) == False (below 0.99 target)."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from slo_generator.sli import AvailabilitySLI
            from slo_generator.slo import SLO

            slo = SLO("test", 0.99, AvailabilitySLI(), 30)
            assert slo.is_compliant(0.989) is False
        finally:
            sys.path[:] = old_path

    def test_func_failure_slo_target_zero(self):
        """SLO(target=0.0) raises ValueError."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from slo_generator.sli import AvailabilitySLI
            from slo_generator.slo import SLO

            with pytest.raises(ValueError):
                SLO("test", 0.0, AvailabilitySLI(), 30)
        finally:
            sys.path[:] = old_path
