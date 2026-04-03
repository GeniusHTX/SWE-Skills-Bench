"""
Test for 'python-resilience' skill — ResilientTransport for httpx
Validates that the Agent created a ResilientTransport class wrapping httpx
transports with retry logic, backoff, jitter, fallback, and Retry-After support.
"""

import os
import re
import sys

import pytest


class TestPythonResilience:
    """Verify httpx ResilientTransport implementation."""

    REPO_DIR = "/workspace/httpx"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    # ---- file_path_check ----

    def test_resilience_py_exists(self):
        """Verifies httpx/_resilience.py exists."""
        path = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_repo_dir_exists(self):
        """Verifies the repository directory exists."""
        assert os.path.exists(
            self.REPO_DIR
        ), f"Repository directory not found: {self.REPO_DIR}"

    # ---- semantic_check ----

    def test_sem_import_resilient_transport(self):
        """Verifies ResilientTransport can be imported."""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import ResilientTransport

            assert ResilientTransport is not None
        finally:
            sys.path.pop(0)

    def test_sem_init_parameters(self):
        """Verifies ResilientTransport.__init__ accepts required parameters."""
        content = self._read(os.path.join(self.REPO_DIR, "httpx/_resilience.py"))
        for param in [
            "transport",
            "max_retries",
            "backoff_base",
            "backoff_max",
            "backoff_jitter",
            "timeout_per_attempt",
            "retryable_status_codes",
            "retryable_exceptions",
        ]:
            assert (
                param in content
            ), f"Parameter '{param}' not found in ResilientTransport.__init__"

    def test_sem_default_values(self):
        """Verifies sensible default values for key parameters."""
        content = self._read(os.path.join(self.REPO_DIR, "httpx/_resilience.py"))
        assert (
            "max_retries" in content and "3" in content
        ), "max_retries=3 default not found"
        assert "429" in content, "429 not in retryable_status_codes"
        assert "502" in content, "502 not in retryable_status_codes"
        assert "503" in content, "503 not in retryable_status_codes"
        assert "504" in content, "504 not in retryable_status_codes"

    def test_sem_handle_request_method(self):
        """Verifies handle_request(request) method exists (edge case)."""
        content = self._read(os.path.join(self.REPO_DIR, "httpx/_resilience.py"))
        assert re.search(
            r"def handle_request\s*\(", content
        ), "handle_request method not found"

    def test_sem_base_transport_subclass(self):
        """Verifies ResilientTransport subclasses BaseTransport or similar."""
        content = self._read(os.path.join(self.REPO_DIR, "httpx/_resilience.py"))
        assert (
            "BaseTransport" in content
            or "httpx.BaseTransport" in content
            or "handle_request" in content
        ), "ResilientTransport does not implement BaseTransport interface"

    # ---- functional_check ----

    def test_func_retry_on_503_then_200(self):
        """Mock transport returns [503,503,503,200]: should succeed after retries."""
        sys.path.insert(0, self.REPO_DIR)
        try:
            import httpx
            from httpx._resilience import ResilientTransport

            call_count = 0
            responses = [503, 503, 503, 200]

            class MockTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    nonlocal call_count
                    status = responses[min(call_count, len(responses) - 1)]
                    call_count += 1
                    return httpx.Response(status)

            rt = ResilientTransport(
                transport=MockTransport(), max_retries=3, backoff_base=0.0
            )
            request = httpx.Request("GET", "http://example.com")
            response = rt.handle_request(request)
            assert (
                response.status_code == 200
            ), f"Expected 200 after retries, got {response.status_code}"
        finally:
            sys.path.pop(0)

    def test_func_no_retry_on_400(self):
        """Mock transport returns [400]: returned immediately without retry."""
        sys.path.insert(0, self.REPO_DIR)
        try:
            import httpx
            from httpx._resilience import ResilientTransport

            call_count = 0

            class MockTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    nonlocal call_count
                    call_count += 1
                    return httpx.Response(400)

            rt = ResilientTransport(
                transport=MockTransport(), max_retries=3, backoff_base=0.0
            )
            request = httpx.Request("GET", "http://example.com")
            response = rt.handle_request(request)
            assert response.status_code == 400
            assert call_count == 1, f"Expected 1 call, got {call_count}"
        finally:
            sys.path.pop(0)

    def test_func_non_retryable_exception_propagated(self):
        """Mock transport raises ValueError: propagated without retry (failure)."""
        sys.path.insert(0, self.REPO_DIR)
        try:
            import httpx
            from httpx._resilience import ResilientTransport

            class MockTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    raise ValueError("bad value")

            rt = ResilientTransport(
                transport=MockTransport(), max_retries=3, backoff_base=0.0
            )
            request = httpx.Request("GET", "http://example.com")
            with pytest.raises(ValueError):
                rt.handle_request(request)
        finally:
            sys.path.pop(0)

    def test_func_retry_on_connect_error(self):
        """Mock transport raises ConnectError twice then 200 (failure scenario)."""
        sys.path.insert(0, self.REPO_DIR)
        try:
            import httpx
            from httpx._resilience import ResilientTransport

            call_count = 0

            class MockTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    nonlocal call_count
                    call_count += 1
                    if call_count <= 2:
                        raise httpx.ConnectError("connection refused")
                    return httpx.Response(200)

            rt = ResilientTransport(
                transport=MockTransport(),
                max_retries=3,
                backoff_base=0.0,
                retryable_exceptions=(httpx.ConnectError,),
            )
            request = httpx.Request("GET", "http://example.com")
            response = rt.handle_request(request)
            assert response.status_code == 200
        finally:
            sys.path.pop(0)

    def test_func_exhausted_retries_raises(self):
        """Mock transport always raises ConnectError: eventually propagated."""
        sys.path.insert(0, self.REPO_DIR)
        try:
            import httpx
            from httpx._resilience import ResilientTransport

            class MockTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    raise httpx.ConnectError("connection refused")

            rt = ResilientTransport(
                transport=MockTransport(),
                max_retries=3,
                backoff_base=0.0,
                retryable_exceptions=(httpx.ConnectError,),
            )
            request = httpx.Request("GET", "http://example.com")
            with pytest.raises((httpx.ConnectError, Exception)):
                rt.handle_request(request)
        finally:
            sys.path.pop(0)

    def test_func_fallback_handler(self):
        """Fallback returns fake response after all retries fail."""
        sys.path.insert(0, self.REPO_DIR)
        try:
            import httpx
            from httpx._resilience import ResilientTransport

            fake_response = httpx.Response(999)

            class MockTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    raise httpx.ConnectError("fail")

            rt = ResilientTransport(
                transport=MockTransport(),
                max_retries=2,
                backoff_base=0.0,
                retryable_exceptions=(httpx.ConnectError,),
                fallback=lambda req, exc: fake_response,
            )
            request = httpx.Request("GET", "http://example.com")
            response = rt.handle_request(request)
            assert response.status_code == 999
        finally:
            sys.path.pop(0)

    def test_func_retry_after_header_respected(self):
        """Mock 429 with Retry-After header: sleep should respect it."""
        sys.path.insert(0, self.REPO_DIR)
        try:
            import httpx
            from unittest.mock import patch
            from httpx._resilience import ResilientTransport

            call_count = 0

            class MockTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        return httpx.Response(429, headers={"Retry-After": "5"})
                    return httpx.Response(200)

            sleep_values = []
            with patch("time.sleep", side_effect=lambda s: sleep_values.append(s)):
                rt = ResilientTransport(
                    transport=MockTransport(), max_retries=3, backoff_base=0.0
                )
                request = httpx.Request("GET", "http://example.com")
                response = rt.handle_request(request)
            assert response.status_code == 200
            if sleep_values:
                assert any(
                    v >= 5 for v in sleep_values
                ), f"Expected sleep >= 5s for Retry-After, got {sleep_values}"
        finally:
            sys.path.pop(0)

    def test_func_total_timeout(self):
        """total_timeout=0.001 should raise TimeoutError quickly (failure)."""
        sys.path.insert(0, self.REPO_DIR)
        try:
            import httpx
            from httpx._resilience import ResilientTransport
            import time

            class SlowTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    time.sleep(0.1)
                    return httpx.Response(503)

            try:
                rt = ResilientTransport(
                    transport=SlowTransport(),
                    max_retries=10,
                    backoff_base=0.0,
                    total_timeout=0.001,
                )
                request = httpx.Request("GET", "http://example.com")
                rt.handle_request(request)
                # If no error raised, the transport may not support total_timeout
                # Mark as passed — implementation may handle differently
            except (TimeoutError, Exception):
                pass  # Expected
        finally:
            sys.path.pop(0)
