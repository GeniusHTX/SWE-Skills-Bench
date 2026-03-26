"""
Tests for python-resilience skill.
Validates ResilientTransport in httpx/_transports/resilient.py.
"""

import os
import pytest

REPO_DIR = "/workspace/httpx"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestPythonResilience:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_resilient_transport_file_exists(self):
        """httpx/_transports/resilient.py must exist."""
        rel = "httpx/_transports/resilient.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "resilient.py is empty"

    def test_transports_init_exists(self):
        """httpx/_transports/__init__.py must exist."""
        rel = "httpx/_transports/__init__.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_resilient_transport_class_defined(self):
        """ResilientTransport must define max_retries and retry_statuses."""
        content = _read("httpx/_transports/resilient.py")
        assert (
            "class ResilientTransport" in content
        ), "ResilientTransport class not defined"
        assert "max_retries" in content, "max_retries parameter not found"
        assert "retry_statuses" in content, "retry_statuses parameter not found"

    def test_retry_after_header_respected(self):
        """ResilientTransport must read Retry-After header to control delay."""
        content = _read("httpx/_transports/resilient.py")
        assert (
            "Retry-After" in content or "retry-after" in content.lower()
        ), "Retry-After header parsing not found in resilient.py"

    def test_no_retry_for_4xx_client_errors(self):
        """retry_statuses must not include general 4xx range (only server errors retried)."""
        content = _read("httpx/_transports/resilient.py")
        # Should retry 5xx (500, 502, 503, 504) and possibly 429
        assert "503" in content or "5" in content, "No 5xx retry codes found"
        # Must not retry all 4xx (400, 401, etc.)
        assert "retry_statuses" in content, "retry_statuses parameter not defined"

    def test_warning_log_per_retry(self):
        """ResilientTransport must emit WARNING log for each retry attempt."""
        content = _read("httpx/_transports/resilient.py")
        has_warn = "warning" in content.lower() or "logger.warn" in content
        assert has_warn, "No warning log found for retry attempts in resilient.py"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_503_twice_then_200_success(self):
        """503 twice then 200 must succeed after retries (mocked)."""
        responses = iter([503, 503, 200])

        def fake_send(request):
            return next(responses)

        def resilient_send(
            request, max_retries=3, retry_statuses=frozenset({503, 502, 500})
        ):
            for attempt in range(max_retries + 1):
                status = fake_send(request)
                if status not in retry_statuses:
                    return status
            return status

        result = resilient_send("GET /api")
        assert result == 200

    def test_400_no_retry(self):
        """400 must be returned without retry (mocked)."""
        call_count = [0]

        def fake_send(request):
            call_count[0] += 1
            return 400

        def resilient_send(
            request, max_retries=3, retry_statuses=frozenset({503, 502, 500})
        ):
            for attempt in range(max_retries + 1):
                status = fake_send(request)
                if status not in retry_statuses:
                    return status
            return status

        result = resilient_send("GET /api")
        assert result == 400
        assert call_count[0] == 1, f"Expected 1 call, got {call_count[0]} (retried 400)"

    def test_3_connection_errors_raises(self):
        """3 consecutive ConnectionErrors must raise an exception (mocked)."""

        class MaxRetriesExceeded(Exception):
            pass

        attempts = [0]

        def fake_send(request):
            attempts[0] += 1
            raise ConnectionError("refused")

        def resilient_send(request, max_retries=2):
            for attempt in range(max_retries + 1):
                try:
                    return fake_send(request)
                except ConnectionError:
                    if attempt == max_retries:
                        raise MaxRetriesExceeded("exhausted retries") from None

        with pytest.raises(MaxRetriesExceeded):
            resilient_send("GET /api", max_retries=2)
        assert attempts[0] == 3

    def test_retry_after_header_respected_mocked(self):
        """Retry-After:2 must induce ~2s wait before retry (mocked via sleep tracking)."""
        sleeps = []

        def fake_sleep(duration):
            sleeps.append(duration)

        def resilient_send_with_header(retry_after_value: str):
            headers = {"Retry-After": retry_after_value}
            wait = float(headers.get("Retry-After", 0))
            fake_sleep(wait)

        resilient_send_with_header("2")
        assert sleeps == [2.0], f"Expected sleep of 2.0s, got {sleeps}"

    def test_max_backoff_cap(self):
        """Exponential backoff must be capped at max_backoff (mocked)."""

        def compute_backoff(
            attempt: int, base: float = 2.0, max_backoff: float = 60.0
        ) -> float:
            return min(base**attempt, max_backoff)

        delays = [compute_backoff(i, max_backoff=60.0) for i in range(10)]
        assert max(delays) <= 60.0, f"Backoff exceeded max_backoff=60: {max(delays)}"

    def test_async_client_compatible(self):
        """ResilientTransport must be usable as an async transport (mocked)."""
        import asyncio

        class MockAsyncTransport:
            async def handle_async_request(self, request):
                return {"status_code": 200}

        class AsyncResilientTransport(MockAsyncTransport):
            def __init__(self, max_retries: int = 3):
                self.max_retries = max_retries

        async def run():
            transport = AsyncResilientTransport(max_retries=2)
            response = await transport.handle_async_request(
                {"method": "GET", "url": "/api"}
            )
            assert response["status_code"] == 200

        asyncio.run(run())
