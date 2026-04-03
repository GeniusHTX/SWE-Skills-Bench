"""
Test for 'python-resilience' skill — Python Resilience Patterns
Validates retry decorator, circuit breaker, bulkhead, and timeout patterns:
file existence, semantic signatures, and functional behavior via direct
import with mocked dependencies.
"""

import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest


class TestPythonResilience:
    """Verify Python resilience patterns: retry, circuit breaker, bulkhead, timeout."""

    REPO_DIR = "/workspace/httpx"

    # ── helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    @classmethod
    def _add_to_path(cls):
        examples_dir = os.path.join(cls.REPO_DIR, "examples")
        if examples_dir not in sys.path:
            sys.path.insert(0, examples_dir)
        if cls.REPO_DIR not in sys.path:
            sys.path.insert(0, cls.REPO_DIR)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_retry_and_circuit_breaker_py_exist(self):
        """examples/resilience/retry.py and circuit_breaker.py must exist."""
        for name in ("retry.py", "circuit_breaker.py"):
            path = os.path.join(self.REPO_DIR, "examples", "resilience", name)
            assert os.path.isfile(path), f"{path} does not exist"
            assert os.path.getsize(path) > 0, f"{name} is empty"

    def test_bulkhead_timeout_and_test_exist(self):
        """bulkhead.py, timeout.py, and tests/test_resilience.py must exist."""
        for name in ("bulkhead.py", "timeout.py"):
            path = os.path.join(self.REPO_DIR, "examples", "resilience", name)
            assert os.path.isfile(path), f"{path} does not exist"
        test_path = os.path.join(self.REPO_DIR, "tests", "test_resilience.py")
        assert os.path.isfile(test_path), f"{test_path} does not exist"

    def test_init_py_exists(self):
        """examples/resilience/__init__.py must exist."""
        path = os.path.join(self.REPO_DIR, "examples", "resilience", "__init__.py")
        assert os.path.isfile(path), f"{path} does not exist"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_retry_decorator_accepts_params(self):
        """retry() must accept max_attempts, backoff_factor, exceptions."""
        content = self._read_file(
            os.path.join(self.REPO_DIR, "examples", "resilience", "retry.py")
        )
        assert "def retry" in content, "retry function not defined"
        assert "max_attempts" in content, "max_attempts parameter missing"
        assert "backoff_factor" in content, "backoff_factor parameter missing"
        assert "functools.wraps" in content or "wraps" in content, (
            "functools.wraps not used"
        )

    def test_circuit_breaker_has_states_and_threshold(self):
        """CircuitBreaker must define CLOSED/OPEN/HALF_OPEN states."""
        content = self._read_file(
            os.path.join(self.REPO_DIR, "examples", "resilience", "circuit_breaker.py")
        )
        assert "CircuitBreaker" in content, "CircuitBreaker class not defined"
        assert "failure_threshold" in content, "failure_threshold missing"
        for state in ("CLOSED", "OPEN", "HALF_OPEN"):
            assert state in content, f"{state} state not defined"

    def test_bulkhead_uses_threading_semaphore(self):
        """Bulkhead must use threading.Semaphore and define BulkheadFullError."""
        content = self._read_file(
            os.path.join(self.REPO_DIR, "examples", "resilience", "bulkhead.py")
        )
        assert "Semaphore" in content, "Semaphore not used in bulkhead"
        assert "BulkheadFullError" in content, "BulkheadFullError not defined"

    def test_exponential_backoff_formula(self):
        """retry.py must use exponential backoff (** operator) with time.sleep."""
        content = self._read_file(
            os.path.join(self.REPO_DIR, "examples", "resilience", "retry.py")
        )
        assert "**" in content or "pow" in content, (
            "No exponential backoff formula (** or pow) found"
        )
        assert "time.sleep" in content or "sleep" in content, (
            "time.sleep not called for backoff delay"
        )

    # ── functional_check (import) ────────────────────────────────────────

    def test_retry_fails_twice_then_succeeds(self):
        """@retry(3) on function failing twice then returning 'ok' must succeed."""
        self._add_to_path()
        try:
            from resilience.retry import retry
        except ImportError as exc:
            pytest.skip(f"Cannot import retry: {exc}")

        call_count = 0

        @retry(max_attempts=3, exceptions=(ValueError,))
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"

        with patch("time.sleep"):
            result = flaky()
        assert result == "ok"
        assert call_count == 3

    def test_retry_all_attempts_exhausted_raises(self):
        """@retry(3) on always-failing function must propagate ValueError."""
        self._add_to_path()
        try:
            from resilience.retry import retry
        except ImportError as exc:
            pytest.skip(f"Cannot import retry: {exc}")

        @retry(max_attempts=3, exceptions=(ValueError,))
        def always_fail():
            raise ValueError("boom")

        with patch("time.sleep"):
            with pytest.raises(ValueError, match="boom"):
                always_fail()

    def test_circuit_breaker_opens_after_threshold(self):
        """CircuitBreaker must transition to OPEN after failure_threshold failures."""
        self._add_to_path()
        try:
            from resilience.circuit_breaker import CircuitBreaker, CircuitOpenError
        except ImportError as exc:
            pytest.skip(f"Cannot import CircuitBreaker: {exc}")

        cb = CircuitBreaker(failure_threshold=3, reset_timeout=10)
        for _ in range(3):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except (ValueError, Exception):
                pass
        state = str(cb.state).upper() if hasattr(cb, "state") else ""
        assert "OPEN" in state, f"Expected OPEN state, got {state}"

    def test_circuit_open_raises_circuit_open_error(self):
        """Calling through open circuit must raise CircuitOpenError."""
        self._add_to_path()
        try:
            from resilience.circuit_breaker import CircuitBreaker, CircuitOpenError
        except ImportError as exc:
            pytest.skip(f"Cannot import CircuitBreaker: {exc}")

        cb = CircuitBreaker(failure_threshold=1, reset_timeout=60)
        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except (ValueError, Exception):
            pass
        mock_fn = MagicMock()
        with pytest.raises(CircuitOpenError):
            cb.call(mock_fn)
        mock_fn.assert_not_called()

    def test_bulkhead_full_raises_error(self):
        """Bulkhead at capacity must raise BulkheadFullError."""
        self._add_to_path()
        try:
            from resilience.bulkhead import Bulkhead, BulkheadFullError
        except ImportError as exc:
            pytest.skip(f"Cannot import Bulkhead: {exc}")

        bh = Bulkhead(max_concurrent=1)
        # Pre-acquire the semaphore to simulate full capacity
        if hasattr(bh, "_semaphore"):
            bh._semaphore.acquire()
        with pytest.raises(BulkheadFullError):
            bh.call(lambda: None)

    def test_timeout_decorator_raises_timeout_error(self):
        """@timeout(0.1) on slow function must raise TimeoutError quickly."""
        self._add_to_path()
        try:
            from resilience.timeout import timeout
        except ImportError as exc:
            pytest.skip(f"Cannot import timeout: {exc}")

        @timeout(seconds=0.1)
        def slow_fn():
            time.sleep(5)

        start = time.time()
        with pytest.raises((TimeoutError, Exception)):
            slow_fn()
        elapsed = time.time() - start
        assert elapsed < 1.0, f"Timeout took too long: {elapsed:.2f}s"
