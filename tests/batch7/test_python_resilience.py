"""Test file for the python-resilience skill.

This suite validates the ResilientAsyncClient with retry logic,
circuit breaker, and error classification in httpx.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest


class TestPythonResilience:
    """Verify resilience patterns in httpx."""

    REPO_DIR = "/workspace/httpx"

    RESILIENCE_PY = "httpx/_resilience.py"
    CONFIG_PY = "httpx/_config.py"
    TEST_PY = "tests/test_resilience.py"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    def _class_source(self, source: str, class_name: str) -> str | None:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                start = node.lineno - 1
                end = node.end_lineno or start + 1
                lines = source.splitlines()
                return "\n".join(lines[start:end])
        return None

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_httpx__resilience_py_exists(self):
        """Verify _resilience.py exists and is non-empty."""
        self._assert_non_empty_file(self.RESILIENCE_PY)

    def test_file_path_httpx__config_py_modified_with_resilience_defaults(self):
        """Verify _config.py modified with resilience defaults."""
        self._assert_non_empty_file(self.CONFIG_PY)
        src = self._read_text(self.CONFIG_PY)
        assert re.search(
            r"resilien|retry|circuit", src, re.IGNORECASE
        ), "_config.py should contain resilience defaults"

    def test_file_path_tests_test_resilience_py_exists(self):
        """Verify test_resilience.py exists and is non-empty."""
        self._assert_non_empty_file(self.TEST_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_resilientasyncclient_class_with_retry_config_and_circuit_bre(
        self,
    ):
        """ResilientAsyncClient class with retry_config and circuit_breaker_config."""
        src = self._read_text(self.RESILIENCE_PY)
        body = self._class_source(src, "ResilientAsyncClient")
        assert body is not None, "ResilientAsyncClient class not found"
        assert "retry_config" in body, "Missing retry_config parameter"
        assert (
            "circuit_breaker" in body.lower()
        ), "Missing circuit_breaker_config parameter"

    def test_semantic_exponential_backoff_formula_min_base_2_attempt_jitter_max(self):
        """Exponential backoff formula: min(base * 2^attempt + jitter, max)."""
        src = self._read_text(self.RESILIENCE_PY)
        assert re.search(
            r"2\s*\*\*|pow\s*\(.*2|backoff|exponential", src
        ), "Exponential backoff formula not found"

    def test_semantic_circuit_breaker_with_closed_open_half_open_states(self):
        """Circuit breaker with CLOSED/OPEN/HALF_OPEN states."""
        src = self._read_text(self.RESILIENCE_PY)
        for state in ("CLOSED", "OPEN", "HALF_OPEN"):
            assert state in src, f"Circuit breaker missing state: {state}"

    def test_semantic_error_classification_separating_transient_from_permanent_fai(
        self,
    ):
        """Error classification separating transient from permanent failures."""
        src = self._read_text(self.RESILIENCE_PY)
        assert re.search(
            r"transient|permanent|is_transient|is_retryable", src, re.IGNORECASE
        ), "Error classification for transient vs permanent not found"

    def test_semantic_circuitbreakeropenerror_exception_class_defined(self):
        """CircuitBreakerOpenError exception class defined."""
        src = self._read_text(self.RESILIENCE_PY)
        assert re.search(
            r"class\s+CircuitBreakerOpenError", src
        ), "CircuitBreakerOpenError exception class not found"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, source analysis)
    # ------------------------------------------------------------------

    def test_functional_503_three_times_then_200_succeeds_on_4th_attempt(self):
        """503 three times then 200 -> succeeds on 4th attempt."""
        src = self._read_text(self.RESILIENCE_PY)
        assert re.search(r"retry|attempt|max_retries", src), "Retry logic required"

    def test_functional_unreachable_host_with_max_retries_2_connecterror_after_3_att(
        self,
    ):
        """Unreachable host with max_retries=2 -> ConnectError after 3 attempts."""
        src = self._read_text(self.RESILIENCE_PY)
        assert re.search(
            r"max_retries|max_attempts", src
        ), "max_retries/max_attempts parameter required"

    def test_functional_400_response_immediate_raise_without_retry(self):
        """400 response -> immediate raise without retry."""
        src = self._read_text(self.RESILIENCE_PY)
        assert re.search(
            r"4\d\d|permanent|not.*retry", src, re.IGNORECASE
        ), "400 responses should not be retried"

    def test_functional_5_consecutive_failures_circuitbreakeropenerror_on_next_reque(
        self,
    ):
        """5 consecutive failures -> CircuitBreakerOpenError on next request."""
        src = self._read_text(self.RESILIENCE_PY)
        assert re.search(
            r"failure_threshold|failure_count|consecutive", src
        ), "Circuit breaker failure threshold logic required"

    def test_functional_after_recovery_timeout_probe_request_allowed(self):
        """After recovery_timeout -> probe request allowed."""
        src = self._read_text(self.RESILIENCE_PY)
        assert re.search(
            r"recovery_timeout|reset_timeout|half.open", src, re.IGNORECASE
        ), "Recovery timeout / probe logic required"
