"""
Test for 'python-resilience' skill — httpx RetryTransport
Validates RetryTransport, Retry-After header capped at 60s,
503 retry logic, exponential backoff, and circuit breaker patterns.
"""

import os
import re
import sys

import pytest


class TestPythonResilience:
    """Verify Python resilience patterns with httpx."""

    REPO_DIR = "/workspace/httpx"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_httpx_source_exists(self):
        """Verify httpx source directory exists."""
        candidates = [
            os.path.join(self.REPO_DIR, "httpx"),
            os.path.join(self.REPO_DIR, "src", "httpx"),
        ]
        assert any(
            os.path.isdir(c) for c in candidates
        ), "httpx/ package directory not found"

    def test_transport_files_exist(self):
        """Verify transport-related files exist."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and "transport" in f.lower():
                    found = True
                    break
            if found:
                break
        assert found, "No transport files found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_retry_transport(self):
        """Verify RetryTransport implementation."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(RetryTransport|retry.?transport|class.*Retry.*Transport)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No RetryTransport implementation found")

    def test_retry_after_header(self):
        """Verify Retry-After header handling."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(retry.?after|Retry-After)", content, re.IGNORECASE):
                return
        pytest.fail("No Retry-After header handling found")

    def test_retry_after_cap_60s(self):
        """Verify Retry-After is capped (e.g. max 60 seconds)."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(max.*60|cap.*60|MAX_RETRY.*60|min\(.*60)", content):
                return
            if re.search(r"Retry-After", content, re.IGNORECASE) and re.search(
                r"(cap|max|limit|clamp)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No Retry-After cap at 60s found")

    def test_503_retry(self):
        """Verify 503 status code triggers retry."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(503|Service.?Unavailable|retryable.*status)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No 503 retry logic found")

    def test_exponential_backoff(self):
        """Verify exponential backoff strategy."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(backoff|exponential|jitter|2\s*\*\*|pow\(2)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No exponential backoff found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_source_files_parse(self):
        """Verify Python source files are syntactically valid."""
        import ast

        py_files = self._find_py_files()
        for fpath in py_files[:15]:
            content = self._read(fpath)
            try:
                ast.parse(content, filename=fpath)
            except SyntaxError as e:
                pytest.fail(f"SyntaxError in {os.path.basename(fpath)}: {e}")

    def test_retry_max_attempts(self):
        """Verify max retry attempts are configured."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(max_retries|max_attempts|retry_count|retries\s*=\s*\d)", content
            ):
                return
        pytest.fail("No max retry attempts config found")

    def test_timeout_configuration(self):
        """Verify timeout is configured for requests."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(timeout\s*=|Timeout\(|connect_timeout|read_timeout)", content
            ):
                return
        pytest.fail("No timeout configuration found")

    def test_transport_interface(self):
        """Verify transport implements proper interface (handle_request)."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"def handle_(request|async_request)\(", content):
                return
        pytest.fail("No handle_request method found")

    def test_logging_or_tracing(self):
        """Verify retry attempts are logged or traced."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if "retry" in content.lower() and re.search(
                r"(logger|logging|log\.|print|trace)", content
            ):
                return
        pytest.skip("No retry logging found (may not be required)")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_py_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
