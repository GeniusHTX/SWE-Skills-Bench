"""
Test for 'python-resilience' skill — HTTP Resilience Library
Validates that the Agent implemented retry transport, circuit breaker,
and bulkhead patterns for HTTPX-based HTTP resilience.
"""

import os
import re
import sys

import pytest


class TestPythonResilience:
    """Verify HTTP resilience implementation."""

    REPO_DIR = "/workspace/httpx"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_resilience_module_files_exist(self):
        """Verify retry.py and circuit_breaker.py exist in src/http_resilience/."""
        for rel in ("src/http_resilience/retry.py",
                     "src/http_resilience/circuit_breaker.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_bulkhead_module_exists(self):
        """Verify src/http_resilience/bulkhead.py exists."""
        path = os.path.join(self.REPO_DIR, "src/http_resilience/bulkhead.py")
        assert os.path.isfile(path), "Missing: src/http_resilience/bulkhead.py"

    # ── semantic_check ──────────────────────────────────────────────

    def test_retry_transport_constructor_params(self):
        """Verify RetryTransport accepts max_retries, retry_on, and backoff_factor."""
        content = self._read(os.path.join(self.REPO_DIR, "src/http_resilience/retry.py"))
        assert content, "retry.py is empty or unreadable"
        for kw in ("max_retries", "retry_on", "backoff_factor"):
            assert kw in content, f"'{kw}' not found in retry.py"

    def test_circuit_breaker_state_enum(self):
        """Verify CircuitBreaker uses CLOSED, OPEN, HALF_OPEN state enum."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/http_resilience/circuit_breaker.py"))
        assert content, "circuit_breaker.py is empty or unreadable"
        for state in ("CLOSED", "OPEN", "HALF_OPEN"):
            assert state in content, f"State '{state}' not found in circuit_breaker.py"

    def test_custom_exception_classes_defined(self):
        """Verify MaxRetriesExceeded and CircuitOpenError are defined."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/http_resilience/__init__.py"))
        assert content, "__init__.py is empty or unreadable"
        assert "MaxRetriesExceeded" in content, "MaxRetriesExceeded not found"
        assert "CircuitOpenError" in content, "CircuitOpenError not found"

    def test_bulkhead_semaphore_max_concurrent(self):
        """Verify BulkheadSemaphore accepts max_concurrent and uses a semaphore."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/http_resilience/bulkhead.py"))
        assert content, "bulkhead.py is empty or unreadable"
        assert "max_concurrent" in content, "max_concurrent not found"
        assert "Semaphore" in content, "Semaphore not found"

    # ── functional_check (import) ───────────────────────────────────

    def _skip_unless_importable(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if self.REPO_DIR not in sys.path:
            sys.path.insert(0, self.REPO_DIR)

    def test_retry_503_twice_then_200_calls_mock_three_times(self):
        """503 twice then 200: underlying transport called exactly 3 times."""
        self._skip_unless_importable()
        try:
            import httpx
            from src.http_resilience.retry import RetryTransport
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        call_count = [0]

        def mock_send(request, **kwargs):
            call_count[0] += 1
            status = 503 if call_count[0] < 3 else 200
            return httpx.Response(status)

        transport = RetryTransport(max_retries=3, retry_on=[503])
        transport._inner = type("T", (), {"handle_request": mock_send})()
        transport.handle_request(httpx.Request("GET", "http://test/"))
        assert call_count[0] == 3, f"Expected 3 calls, got {call_count[0]}"

    def test_max_retries_exceeded_on_persistent_503(self):
        """Persistent 503 after max_retries=3 exhaustion raises MaxRetriesExceeded."""
        self._skip_unless_importable()
        try:
            from src.http_resilience import RetryTransport, MaxRetriesExceeded
            import httpx
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        transport = RetryTransport(max_retries=3, retry_on=[503])
        with pytest.raises(MaxRetriesExceeded):
            transport.handle_request(httpx.Request("GET", "http://test/"))

    def test_400_response_not_retried(self):
        """400 response is not retried; underlying transport called exactly once."""
        self._skip_unless_importable()
        try:
            import httpx
            from src.http_resilience.retry import RetryTransport
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        call_count = [0]

        def always_400(req, **kw):
            call_count[0] += 1
            return httpx.Response(400)

        t = RetryTransport(max_retries=3, retry_on=[503])
        t._inner = type("T", (), {"handle_request": always_400})()
        t.handle_request(httpx.Request("GET", "http://test/"))
        assert call_count[0] == 1, f"Expected 1 call, got {call_count[0]}"

    def test_three_failures_open_circuit(self):
        """Three consecutive failures transition CircuitBreaker to OPEN state."""
        self._skip_unless_importable()
        try:
            from src.http_resilience.circuit_breaker import CircuitBreaker, State
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == State.OPEN, f"Expected OPEN, got {cb.state}"

    def test_open_circuit_raises_circuit_open_error(self):
        """Calling CircuitBreaker.call() when OPEN raises CircuitOpenError."""
        self._skip_unless_importable()
        try:
            from src.http_resilience.circuit_breaker import CircuitBreaker
            from src.http_resilience import CircuitOpenError
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=9999)
        cb.record_failure()
        with pytest.raises(CircuitOpenError):
            cb.call(lambda: None)
