"""
Test for 'python-resilience' skill — Python Resilience Patterns
Validates that the Agent implemented a resilient HTTP transport layer
for httpx with retry logic, circuit breaker, and timeout handling.
"""

import os
import re
import subprocess

import pytest

from _dependency_utils import ensure_python_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_python_dependencies(TestPythonResilience.REPO_DIR)


class TestPythonResilience:
    """Verify resilient HTTP transport implementation for httpx."""

    REPO_DIR = "/workspace/httpx"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence and syntax
    # ------------------------------------------------------------------

    def test_resilient_transport_file_exists(self):
        """httpx/_transports/resilient.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "httpx", "_transports", "resilient.py")
        assert os.path.isfile(fpath), "httpx/_transports/resilient.py not found"

    def test_resilient_transport_compiles(self):
        """resilient.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "httpx/_transports/resilient.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error in resilient.py:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L1: Transport class structure
    # ------------------------------------------------------------------

    def test_defines_transport_class(self):
        """resilient.py must define a transport class."""
        content = self._read("httpx", "_transports", "resilient.py")
        assert re.search(
            r"class\s+\w*[Rr]esilient\w*[Tt]ransport", content
        ), "No resilient transport class found"

    def test_transport_wraps_base_transport(self):
        """The resilient transport must accept and wrap an underlying base transport."""
        content = self._read("httpx", "_transports", "resilient.py")
        patterns = [
            r"__init__.*transport",
            r"self\._transport",
            r"self\.transport",
            r"base_transport",
            r"wrapped",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Transport class does not appear to wrap a base transport"

    def test_transport_implements_handle_request_or_handle_async(self):
        """Transport must implement handle_request or handle_async_request (httpx interface)."""
        content = self._read("httpx", "_transports", "resilient.py")
        assert re.search(
            r"def\s+handle_(async_)?request", content
        ), "Transport does not implement handle_request or handle_async_request"

    # ------------------------------------------------------------------
    # L1: Retry configuration
    # ------------------------------------------------------------------

    def test_retry_max_count_configurable(self):
        """Transport must accept a configurable maximum retry count."""
        content = self._read("httpx", "_transports", "resilient.py")
        patterns = [
            r"max_retries",
            r"retry_count",
            r"retries",
            r"max_attempts",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "No configurable retry count parameter found"

    def test_exponential_backoff_present(self):
        """Retry logic must implement exponential backoff."""
        content = self._read("httpx", "_transports", "resilient.py")
        backoff_patterns = [
            r"backoff",
            r"exponential",
            r"\*\*\s*attempt",
            r"2\s*\*\*",
            r"pow\(",
            r"backoff_factor",
            r"delay\s*\*",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in backoff_patterns
        ), "No exponential backoff logic found in retry implementation"

    def test_retries_on_transient_errors(self):
        """Retry logic must handle transient HTTP errors (502/503/504) and connection errors."""
        content = self._read("httpx", "_transports", "resilient.py")
        # Must reference transient status codes or connection error types
        transient_patterns = [
            r"502",
            r"503",
            r"504",
            r"connect",
            r"ConnectionError",
            r"transient",
            r"retry.*status",
            r"status.*retry",
        ]
        matches = sum(
            1 for p in transient_patterns if re.search(p, content, re.IGNORECASE)
        )
        assert matches >= 2, (
            "Retry logic does not appear to handle sufficient transient error types "
            "(expected references to 502/503/504 and connection errors)"
        )

    # ------------------------------------------------------------------
    # L2: Circuit breaker
    # ------------------------------------------------------------------

    def test_circuit_breaker_logic_exists(self):
        """Transport must implement circuit breaker pattern."""
        content = self._read("httpx", "_transports", "resilient.py")
        cb_patterns = [
            r"circuit",
            r"breaker",
            r"CircuitBreaker",
            r"circuit_breaker",
            r"half.?open",
            r"_state",
        ]
        matches = sum(1 for p in cb_patterns if re.search(p, content, re.IGNORECASE))
        assert matches >= 2, "Circuit breaker pattern not sufficiently implemented"

    def test_circuit_breaker_has_threshold_config(self):
        """Circuit breaker must have a configurable failure threshold."""
        content = self._read("httpx", "_transports", "resilient.py")
        patterns = [
            r"failure_threshold",
            r"max_failures",
            r"threshold",
            r"consecutive_failures",
            r"failure_count",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Circuit breaker missing configurable failure threshold"

    def test_circuit_breaker_has_cooldown(self):
        """Circuit breaker must have a cooldown/recovery period."""
        content = self._read("httpx", "_transports", "resilient.py")
        patterns = [
            r"cooldown",
            r"recovery",
            r"reset_timeout",
            r"open_until",
            r"half_open",
            r"recovery_time",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Circuit breaker missing cooldown/recovery period configuration"

    # ------------------------------------------------------------------
    # L2: Timeout handling
    # ------------------------------------------------------------------

    def test_timeout_handling_present(self):
        """Transport must enforce per-request timeouts."""
        content = self._read("httpx", "_transports", "resilient.py")
        timeout_patterns = [
            r"timeout",
            r"Timeout",
            r"TimeoutError",
            r"TimeoutException",
        ]
        assert any(
            re.search(p, content) for p in timeout_patterns
        ), "No timeout handling found in resilient transport"

    # ------------------------------------------------------------------
    # L2: Dynamic import test
    # ------------------------------------------------------------------

    def test_resilient_transport_importable(self):
        """The resilient transport module must be importable without errors."""
        result = subprocess.run(
            ["python", "-c", "from httpx._transports.resilient import *; print('OK')"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            result.returncode == 0
        ), f"Failed to import resilient transport:\n{result.stderr}"
        assert "OK" in result.stdout

    def test_defaults_are_sensible(self):
        """Constructor default values should be present for all config parameters."""
        content = self._read("httpx", "_transports", "resilient.py")
        # Look for __init__ with default parameters
        init_match = re.search(r"def\s+__init__\s*\(([^)]+)\)", content, re.DOTALL)
        assert init_match, "Transport class __init__ not found"
        params = init_match.group(1)
        # Count parameters with defaults (=)
        defaults = re.findall(r"=\s*\S+", params)
        assert len(defaults) >= 3, (
            f"__init__ should have at least 3 configurable parameters with defaults, "
            f"found {len(defaults)}"
        )
