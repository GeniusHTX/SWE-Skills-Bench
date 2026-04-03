"""
Test for 'risk-metrics-calculation' skill — Financial Risk Metrics
Validates VaR, CVaR, Sharpe, MaxDrawdown, Beta calculators with numpy arrays,
mathematical properties, and input validation.
"""

import os
import subprocess
import sys

import pytest


class TestRiskMetricsCalculation:
    """Verify financial risk metric calculators: VaR, CVaR, Sharpe, Drawdown, Beta."""

    REPO_DIR = "/workspace/pyfolio"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _rm(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "examples", "risk_metrics", *parts)

    def _install_deps(self):
        try:
            import numpy  # noqa: F401
        except ImportError:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "numpy"],
                capture_output=True, timeout=60,
            )

    # ── file_path_check ──────────────────────────────────────────────────

    def test_var_and_cvar_exist(self):
        """var.py and cvar.py must exist."""
        for name in ("var.py", "cvar.py"):
            path = self._rm(name)
            assert os.path.isfile(path), f"{path} does not exist"

    def test_sharpe_drawdown_beta_exist(self):
        """sharpe.py, drawdown.py, beta.py must exist."""
        for name in ("sharpe.py", "drawdown.py", "beta.py"):
            path = self._rm(name)
            assert os.path.isfile(path), f"{path} does not exist"

    def test_init_and_test_file_exist(self):
        """__init__.py and tests/test_risk_metrics.py must exist."""
        assert os.path.isfile(self._rm("__init__.py"))
        test_path = os.path.join(self.REPO_DIR, "tests", "test_risk_metrics.py")
        assert os.path.isfile(test_path), f"{test_path} not found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_var_accepts_confidence_parameter(self):
        """var.py must define VaRCalculator.calculate with confidence param."""
        path = self._rm("var.py")
        if not os.path.isfile(path):
            pytest.skip("var.py not found")
        content = self._read_file(path)
        assert "VaRCalculator" in content, "VaRCalculator not defined"
        assert "confidence" in content, "confidence parameter not found"

    def test_sharpe_annualizes_by_sqrt252(self):
        """sharpe.py must annualize by sqrt(252)."""
        path = self._rm("sharpe.py")
        if not os.path.isfile(path):
            pytest.skip("sharpe.py not found")
        content = self._read_file(path)
        assert "252" in content, "252 (trading days) not found in sharpe.py"
        assert "sqrt" in content, "sqrt not found for annualization"

    def test_drawdown_uses_cummax(self):
        """drawdown.py must use cumulative maximum for peak computation."""
        path = self._rm("drawdown.py")
        if not os.path.isfile(path):
            pytest.skip("drawdown.py not found")
        content = self._read_file(path)
        has_cummax = "cummax" in content or "maximum.accumulate" in content or "peak" in content
        assert has_cummax, "No cumulative max / peak computation found"

    def test_calculators_validate_empty_input(self):
        """At least var.py must raise ValueError for empty input."""
        path = self._rm("var.py")
        if not os.path.isfile(path):
            pytest.skip("var.py not found")
        content = self._read_file(path)
        assert "ValueError" in content, "ValueError not found in var.py"

    # ── functional_check ─────────────────────────────────────────────────

    def test_var_95_returns_correct_value(self):
        """VaR at 95% on known returns must be <= -0.05."""
        self._install_deps()
        try:
            import numpy as np
            sys.path.insert(0, self.REPO_DIR)
            from examples.risk_metrics.var import VaRCalculator
        except ImportError:
            pytest.skip("Cannot import VaRCalculator")
        returns = np.array([-0.05] * 5 + [0.01] * 95)
        var = VaRCalculator().calculate(returns, confidence=0.95)
        assert var <= -0.05 + 0.01, f"VaR should be <= -0.04, got {var}"

    def test_cvar_worse_than_var(self):
        """CVaR must be <= VaR (worse loss by definition)."""
        self._install_deps()
        try:
            import numpy as np
            sys.path.insert(0, self.REPO_DIR)
            from examples.risk_metrics.var import VaRCalculator
            from examples.risk_metrics.cvar import CVaRCalculator
        except ImportError:
            pytest.skip("Cannot import VaR/CVaR calculators")
        returns = np.array([-0.05] * 5 + [0.01] * 95)
        var = VaRCalculator().calculate(returns, confidence=0.95)
        cvar = CVaRCalculator().calculate(returns, confidence=0.95)
        assert cvar <= var, f"CVaR ({cvar}) should be <= VaR ({var})"

    def test_sharpe_positive_for_constant_returns(self):
        """Sharpe ratio must be positive for constant positive returns."""
        self._install_deps()
        try:
            import numpy as np
            sys.path.insert(0, self.REPO_DIR)
            from examples.risk_metrics.sharpe import SharpeRatio
        except ImportError:
            pytest.skip("Cannot import SharpeRatio")
        returns = np.ones(252) * 0.001
        sr = SharpeRatio().calculate(returns, risk_free_rate=0.0)
        assert sr > 0, f"Sharpe ratio should be positive, got {sr}"

    def test_beta_identical_series_equals_one(self):
        """Beta of identical portfolio and benchmark returns must be 1.0."""
        self._install_deps()
        try:
            import numpy as np
            sys.path.insert(0, self.REPO_DIR)
            from examples.risk_metrics.beta import BetaCalculator
        except ImportError:
            pytest.skip("Cannot import BetaCalculator")
        returns = np.random.randn(100) * 0.01
        beta = BetaCalculator().calculate(returns, returns)
        assert abs(beta - 1.0) < 0.01, f"Beta should be ~1.0, got {beta}"

    def test_empty_returns_raises_valueerror(self):
        """Empty returns array must raise ValueError."""
        self._install_deps()
        try:
            import numpy as np
            sys.path.insert(0, self.REPO_DIR)
            from examples.risk_metrics.var import VaRCalculator
        except ImportError:
            pytest.skip("Cannot import VaRCalculator")
        with pytest.raises(ValueError):
            VaRCalculator().calculate(np.array([]), confidence=0.95)
