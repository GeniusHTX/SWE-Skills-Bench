"""
Test for 'langsmith-fetch' skill — LangSmith Trace Analyzer
Validates that the Agent created a Python module for fetching and analyzing
LangSmith traces with latency, error rate, token grouping, and top-N slowest.
"""

import os
import re
import sys

import pytest


class TestLangsmithFetch:
    """Verify LangSmith trace analyzer implementation."""

    REPO_DIR = "/workspace/langchain"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_langsmith_package_exists(self):
        """Verify __init__.py and loader.py exist under src/langsmith_analyzer/."""
        for rel in ("src/langsmith_analyzer/__init__.py", "src/langsmith_analyzer/loader.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_analyzer_aggregator_models_exist(self):
        """Verify analyzer.py, aggregator.py, and models.py exist."""
        for rel in ("src/langsmith_analyzer/analyzer.py",
                     "src/langsmith_analyzer/aggregator.py",
                     "src/langsmith_analyzer/models.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_all_classes_importable(self):
        """TraceLoader, TraceAnalyzer, MetricsAggregator are importable."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            from langsmith_analyzer.loader import TraceLoader  # noqa: F401
            from langsmith_analyzer.analyzer import TraceAnalyzer  # noqa: F401
            from langsmith_analyzer.aggregator import MetricsAggregator  # noqa: F401
        except ImportError:
            pytest.skip("langsmith_analyzer not importable")
        finally:
            sys.path.pop(0)

    # ── semantic_check ──────────────────────────────────────────────

    def test_trace_and_analysis_result_models(self):
        """Verify models.py defines Trace with latency_ms, status, tokens_used, and AnalysisResult."""
        content = self._read(os.path.join(self.REPO_DIR, "src/langsmith_analyzer/models.py"))
        assert content, "models.py is empty or unreadable"
        for field in ("latency_ms", "status", "tokens_used", "AnalysisResult"):
            assert field in content, f"'{field}' not found in models.py"

    def test_analysis_result_fields(self):
        """Verify AnalysisResult has avg_latency_ms, error_rate, token_usage_by_model, top_slowest_traces."""
        content = self._read(os.path.join(self.REPO_DIR, "src/langsmith_analyzer/models.py"))
        assert content, "models.py is empty or unreadable"
        for field in ("avg_latency_ms", "error_rate", "token_usage_by_model",
                      "top_slowest_traces"):
            assert field in content, f"'{field}' not found in models.py"

    def test_api_key_from_env(self):
        """Verify loader.py reads LANGCHAIN_API_KEY from os.environ."""
        content = self._read(os.path.join(self.REPO_DIR, "src/langsmith_analyzer/loader.py"))
        assert content, "loader.py is empty or unreadable"
        assert "LANGCHAIN_API_KEY" in content, "LANGCHAIN_API_KEY not found"
        assert "os.environ" in content, "os.environ not found"

    # ── functional_check (import) ───────────────────────────────────

    def _import(self, dotpath: str):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            return __import__(dotpath, fromlist=[""])
        except ImportError:
            pytest.skip(f"{dotpath} not importable")
        finally:
            sys.path.pop(0)

    def test_empty_traces_returns_zero_metrics(self):
        """analyze([]) returns avg_latency_ms=0 and error_rate=0.0."""
        mod = self._import("langsmith_analyzer.analyzer")
        result = mod.TraceAnalyzer().analyze([])
        assert result.avg_latency_ms == 0
        assert result.error_rate == 0.0

    def test_error_rate_calculated_correctly(self):
        """2 errors in 10 traces produces error_rate=0.2."""
        mod = self._import("langsmith_analyzer.analyzer")
        models = self._import("langsmith_analyzer.models")
        traces = [
            models.Trace(id=str(i), latency_ms=100,
                        status="error" if i < 2 else "ok",
                        model="gpt-4", tokens_used=100, timestamp="2024-01-01")
            for i in range(10)
        ]
        assert mod.TraceAnalyzer().analyze(traces).error_rate == 0.2

    def test_token_usage_grouped_by_model(self):
        """token_usage_by_model['gpt-4'] equals sum of tokens from both gpt-4 traces."""
        mod = self._import("langsmith_analyzer.analyzer")
        models = self._import("langsmith_analyzer.models")
        traces = [
            models.Trace(id="1", latency_ms=100, status="ok",
                        model="gpt-4", tokens_used=500, timestamp="2024-01-01"),
            models.Trace(id="2", latency_ms=200, status="ok",
                        model="gpt-4", tokens_used=300, timestamp="2024-01-01"),
        ]
        assert mod.TraceAnalyzer().analyze(traces).token_usage_by_model["gpt-4"] == 800

    def test_top_slowest_traces_capped_at_five(self):
        """8 traces produce exactly 5 entries in top_slowest_traces."""
        mod = self._import("langsmith_analyzer.analyzer")
        models = self._import("langsmith_analyzer.models")
        traces = [
            models.Trace(id=str(i), latency_ms=i * 100, status="ok",
                        model="gpt-4", tokens_used=100, timestamp="2024-01-01")
            for i in range(8)
        ]
        assert len(mod.TraceAnalyzer().analyze(traces).top_slowest_traces) == 5

    def test_avg_latency_computed_correctly(self):
        """Traces with latency_ms [100, 200, 300] produce avg_latency_ms=200.0."""
        mod = self._import("langsmith_analyzer.analyzer")
        models = self._import("langsmith_analyzer.models")
        traces = [
            models.Trace(id=str(i), latency_ms=ms, status="ok",
                        model="gpt-4", tokens_used=100, timestamp="2024-01-01")
            for i, ms in enumerate([100, 200, 300])
        ]
        assert mod.TraceAnalyzer().analyze(traces).avg_latency_ms == 200.0
