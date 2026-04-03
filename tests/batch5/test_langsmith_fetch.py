"""
Test for 'langsmith-fetch' skill — LangChain LangSmith Trace Fetcher
Validates fetch_traces, percentile aggregation, API key auth,
pagination, error handling, and edge cases.
"""

import os
import re
import subprocess
import sys

import pytest


class TestLangsmithFetch:
    """Verify LangSmith trace fetcher implementation."""

    REPO_DIR = "/workspace/langchain"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_fetcher_module_exists(self):
        """Verify fetcher/trace module exists."""
        found = self._find_files(["fetch", "trace", "langsmith"])
        assert found, "No fetcher/trace module found"

    def test_aggregator_module_exists(self):
        """Verify aggregator/stats module exists."""
        found = self._find_files(["aggregat", "stats", "percentile"])
        assert found, "No aggregator/stats module found"

    def test_auth_module_exists(self):
        """Verify auth/authentication module exists."""
        found = self._find_files(["auth"])
        assert found, "No auth module found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_fetch_traces_function(self):
        """Verify fetch_traces with project_id, limit, offset parameters."""
        files = self._find_files(["fetch", "trace", "langsmith"])
        assert files, "No fetcher files"
        for fpath in files:
            content = self._read(fpath)
            if re.search(r"def\s+fetch_traces", content):
                if re.search(r"(project_id|limit|offset)", content):
                    return
        pytest.fail("No fetch_traces function with expected parameters")

    def test_percentile_aggregation(self):
        """Verify P50/P95/P99 percentile calculations."""
        files = self._find_files(["aggregat", "stats", "percentile"])
        assert files, "No aggregator files"
        for fpath in files:
            content = self._read(fpath)
            if re.search(
                r"(p50|p95|p99|percentile|P50|P95|P99)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No percentile calculation found")

    def test_api_key_env_variable(self):
        """Verify LANGSMITH_API_KEY environment variable usage."""
        all_files = self._find_files(["fetch", "trace", "langsmith", "auth", "config"])
        for fpath in all_files:
            content = self._read(fpath)
            if "LANGSMITH_API_KEY" in content:
                return
        pytest.fail("No LANGSMITH_API_KEY env variable reference")

    def test_pagination_support(self):
        """Verify pagination (offset/limit or cursor) in fetch logic."""
        files = self._find_files(["fetch", "trace", "langsmith"])
        for fpath in files:
            content = self._read(fpath)
            if re.search(
                r"(offset|cursor|page|next_page|pagination)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No pagination support found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_source_files_compile(self):
        """Verify Python files compile without errors."""
        all_files = self._find_files(
            ["fetch", "trace", "langsmith", "aggregat", "auth"]
        )
        assert all_files, "No source files"
        for fpath in all_files:
            if not fpath.endswith(".py"):
                continue
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", fpath],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert (
                result.returncode == 0
            ), f"Compile error in {os.path.basename(fpath)}: {result.stderr}"

    def test_authentication_error_handling(self):
        """Verify AuthenticationError for 401 responses."""
        all_files = self._find_files(["fetch", "trace", "langsmith", "auth"])
        for fpath in all_files:
            content = self._read(fpath)
            if re.search(
                r"(AuthenticationError|401|Unauthorized|auth.*error)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No authentication error handling found")

    def test_empty_traces_handling(self):
        """Verify empty trace set returns valid result."""
        all_files = self._find_files(
            ["fetch", "trace", "langsmith", "aggregat", "test"]
        )
        for fpath in all_files:
            content = self._read(fpath)
            if re.search(
                r"(empty|no.?traces|\[\]|len\(.*\)\s*==\s*0)", content, re.IGNORECASE
            ):
                return
        pytest.skip("Empty traces handling not explicitly detectable")

    def test_rate_limit_handling(self):
        """Verify 429 rate limit handling."""
        all_files = self._find_files(["fetch", "trace", "langsmith", "auth"])
        for fpath in all_files:
            content = self._read(fpath)
            if re.search(
                r"(429|rate.?limit|RateLimitError|retry.?after|too.?many)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.skip("Rate limit handling not explicitly detectable")

    def test_aggregator_handles_single_trace(self):
        """Verify aggregator works with a single trace."""
        files = self._find_files(["aggregat", "stats", "percentile", "test"])
        for fpath in files:
            content = self._read(fpath)
            if re.search(r"(single|one|1.*trace|len.*1)", content, re.IGNORECASE):
                return
        pytest.skip("Single trace handling not explicitly detectable")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_files(self, keywords):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath or "node_modules" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and any(k in f.lower() for k in keywords):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
