"""
Test for 'langsmith-fetch' skill — LangSmith Trace Fetcher
Validates TraceFetcher construction, authentication, error handling,
cost calculation, latency/error filtering, and stats in the langchain repo.
"""

import os
import sys
import re
import pytest
from unittest.mock import MagicMock, patch


class TestLangsmithFetch:
    """Tests for LangSmith trace fetcher in the langchain repo."""

    REPO_DIR = "/workspace/langchain"

    def _ensure_path(self):
        mod_dir = os.path.join(self.REPO_DIR, "langchain", "debug")
        if mod_dir not in sys.path:
            sys.path.insert(0, os.path.join(self.REPO_DIR))

    # --- File Path Checks ---

    def test_trace_fetcher_file_exists(self):
        """Verifies langchain/debug/trace_fetcher.py exists."""
        path = os.path.join(self.REPO_DIR, "langchain", "debug", "trace_fetcher.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_debug_init_exists(self):
        """Verifies langchain/debug/__init__.py exists."""
        path = os.path.join(self.REPO_DIR, "langchain", "debug", "__init__.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    # --- Semantic Checks ---

    def test_sem_imports(self):
        """TraceFetcher and exception classes can be imported."""
        self._ensure_path()
        from langchain.debug.trace_fetcher import (
            TraceFetcher,
            AuthenticationError,
            TraceNotFoundError,
            RateLimitError,
        )

        assert TraceFetcher is not None

    def test_sem_has_methods(self):
        """TraceFetcher has required methods."""
        self._ensure_path()
        from langchain.debug.trace_fetcher import TraceFetcher

        required = [
            "fetch_traces",
            "get_trace",
            "calculate_cost",
            "filter_by_latency",
            "filter_by_error",
            "get_stats",
            "export_to_dataframe",
        ]
        for m in required:
            assert hasattr(TraceFetcher, m), f"Missing method: {m}"

    def test_sem_constructor_params(self):
        """TraceFetcher constructor accepts api_key, project_name, http_client."""
        self._ensure_path()
        from langchain.debug.trace_fetcher import TraceFetcher

        mock_client = MagicMock()
        tf = TraceFetcher(
            api_key="key", project_name="project", http_client=mock_client
        )
        assert tf is not None

    # --- Functional Checks ---

    def test_func_empty_api_key_raises(self):
        """TraceFetcher with empty api_key raises ValueError."""
        self._ensure_path()
        from langchain.debug.trace_fetcher import TraceFetcher

        with pytest.raises(ValueError):
            TraceFetcher(api_key="", project_name="project")

    def test_func_empty_project_raises(self):
        """TraceFetcher with empty project_name raises ValueError."""
        self._ensure_path()
        from langchain.debug.trace_fetcher import TraceFetcher

        with pytest.raises(ValueError):
            TraceFetcher(api_key="key", project_name="")

    def test_func_fetch_traces(self):
        """fetch_traces returns list from mock HTTP client."""
        self._ensure_path()
        from langchain.debug.trace_fetcher import TraceFetcher

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "t1", "latency_ms": 100, "has_error": False},
            {"id": "t2", "latency_ms": 300, "has_error": True},
        ]
        mock_client.get.return_value = mock_response
        tf = TraceFetcher(
            api_key="key", project_name="project", http_client=mock_client
        )
        traces = tf.fetch_traces()
        assert isinstance(traces, list)
        assert len(traces) >= 2

    def test_func_calculate_cost(self):
        """calculate_cost for gpt-4 returns expected value."""
        self._ensure_path()
        from langchain.debug.trace_fetcher import TraceFetcher

        mock_client = MagicMock()
        tf = TraceFetcher(
            api_key="key", project_name="project", http_client=mock_client
        )
        traces = [
            {
                "model": "gpt-4",
                "prompt_tokens": 1000,
                "completion_tokens": 500,
            }
        ]
        cost = tf.calculate_cost(traces)
        # gpt-4: $0.03/1K prompt + $0.06/1K completion → 0.03 + 0.03 = 0.06
        assert abs(cost - 0.06) < 0.01, f"Expected ~0.06 but got {cost}"

    def test_func_filter_by_latency(self):
        """filter_by_latency returns traces within range."""
        self._ensure_path()
        from langchain.debug.trace_fetcher import TraceFetcher

        mock_client = MagicMock()
        tf = TraceFetcher(
            api_key="key", project_name="project", http_client=mock_client
        )
        traces = [
            {"id": "t1", "latency_ms": 100},
            {"id": "t2", "latency_ms": 300},
            {"id": "t3", "latency_ms": 500},
        ]
        filtered = tf.filter_by_latency(traces, min_ms=150, max_ms=350)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "t2"

    def test_func_filter_by_error(self):
        """filter_by_error returns traces with has_error=True."""
        self._ensure_path()
        from langchain.debug.trace_fetcher import TraceFetcher

        mock_client = MagicMock()
        tf = TraceFetcher(
            api_key="key", project_name="project", http_client=mock_client
        )
        traces = [
            {"id": "t1", "has_error": False},
            {"id": "t2", "has_error": True},
        ]
        errors = tf.filter_by_error(traces)
        assert len(errors) == 1
        assert errors[0]["id"] == "t2"

    def test_func_auth_error_401(self):
        """401 HTTP response raises AuthenticationError."""
        self._ensure_path()
        from langchain.debug.trace_fetcher import (
            TraceFetcher,
            AuthenticationError,
        )

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.get.return_value = mock_response
        tf = TraceFetcher(
            api_key="key", project_name="project", http_client=mock_client
        )
        with pytest.raises(AuthenticationError):
            tf.fetch_traces()

    def test_func_not_found_404(self):
        """404 HTTP response raises TraceNotFoundError."""
        self._ensure_path()
        from langchain.debug.trace_fetcher import (
            TraceFetcher,
            TraceNotFoundError,
        )

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response
        tf = TraceFetcher(
            api_key="key", project_name="project", http_client=mock_client
        )
        with pytest.raises(TraceNotFoundError):
            tf.get_trace("nonexistent")

    def test_func_empty_traces_stats(self):
        """get_stats on empty trace list returns zeros."""
        self._ensure_path()
        from langchain.debug.trace_fetcher import TraceFetcher

        mock_client = MagicMock()
        tf = TraceFetcher(
            api_key="key", project_name="project", http_client=mock_client
        )
        stats = tf.get_stats([])
        assert stats.get("count", stats.get("total", 0)) == 0
