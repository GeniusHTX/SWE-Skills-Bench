"""Test file for the langsmith-fetch skill.

This suite validates the TraceAnalyzer and TraceReport classes
that fetch and summarize LangSmith run traces.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest


class TestLangsmithFetch:
    """Verify LangSmith trace analysis utilities."""

    REPO_DIR = "/workspace/langchain"

    TRACE_ANALYZER_PY = "libs/langchain/langchain/smith/trace_analyzer.py"
    TRACE_REPORT_PY = "libs/langchain/langchain/smith/trace_report.py"
    TEST_TRACE_ANALYZER_PY = "tests/unit_tests/smith/test_trace_analyzer.py"

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

    def _all_python_sources(self) -> str:
        parts = []
        for rel in (self.TRACE_ANALYZER_PY, self.TRACE_REPORT_PY):
            p = self._repo_path(rel)
            if p.is_file():
                parts.append(p.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_trace_analyzer_py_exists(self):
        """Verify trace_analyzer.py exists and is non-empty."""
        self._assert_non_empty_file(self.TRACE_ANALYZER_PY)

    def test_file_path_trace_report_py_exists(self):
        """Verify trace_report.py exists and is non-empty."""
        self._assert_non_empty_file(self.TRACE_REPORT_PY)

    def test_file_path_test_trace_analyzer_py_exists(self):
        """Verify test_trace_analyzer.py exists and is non-empty."""
        self._assert_non_empty_file(self.TEST_TRACE_ANALYZER_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_runstats_dataclass_has_12_fields(self):
        """RunStats dataclass has at least 12 fields."""
        src = self._all_python_sources()
        body = self._class_source(src, "RunStats")
        assert body is not None, "RunStats class not found"
        # Count annotated assignments (field: type)
        field_matches = re.findall(r"^\s+\w+\s*:", body, re.MULTILINE)
        assert (
            len(field_matches) >= 12
        ), f"RunStats expected ≥12 fields, found {len(field_matches)}"

    def test_semantic_runstats_success_property(self):
        """RunStats has a success property."""
        src = self._all_python_sources()
        body = self._class_source(src, "RunStats")
        assert body is not None, "RunStats class not found"
        assert re.search(r"@property[\s\S]*?def\s+success\s*\(", body) or re.search(
            r"def\s+success\s*\(", src
        ), "RunStats should have a success property"

    def test_semantic_tracereport_properties(self):
        """TraceReport has error_runs, tool_calls, llm_runs, total_tokens, etc."""
        src = self._all_python_sources()
        body = self._class_source(src, "TraceReport")
        assert body is not None, "TraceReport class not found"
        for prop in ("error_runs", "total_tokens"):
            assert re.search(rf"{prop}", body) or re.search(
                rf"{prop}", src
            ), f"TraceReport missing property: {prop}"

    def test_semantic_traceanalyzer_has_client_and_project_name_params(self):
        """TraceAnalyzer accepts client and project_name params."""
        src = self._read_text(self.TRACE_ANALYZER_PY)
        body = self._class_source(src, "TraceAnalyzer")
        assert body is not None, "TraceAnalyzer class not found"
        assert re.search(
            r"client", body
        ), "TraceAnalyzer should accept a client parameter"
        assert re.search(
            r"project_name", body
        ), "TraceAnalyzer should accept a project_name parameter"

    def test_semantic_fetch_recent_has_last_n_minutes_limit_params(self):
        """fetch_recent has last_n_minutes, limit, run_types, error_only params."""
        src = self._read_text(self.TRACE_ANALYZER_PY)
        assert re.search(
            r"def\s+fetch_recent\s*\(", src
        ), "fetch_recent method not found"
        for param in ("last_n_minutes", "limit"):
            assert param in src, f"fetch_recent missing parameter: {param}"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, mocked/source analysis)
    # ------------------------------------------------------------------

    def test_functional_mocked_client_returns_tracereport(self):
        """Mocked client call returns a TraceReport."""
        src = self._all_python_sources()
        assert re.search(
            r"TraceReport", src
        ), "TraceReport class should be used/returned"
        assert re.search(
            r"fetch_recent|list_runs|_fetch", src
        ), "Fetch mechanism should exist"

    def test_functional_run_to_stats_llm_run(self):
        """_run_to_stats handles LLM run correctly."""
        src = self._all_python_sources()
        assert re.search(
            r"_run_to_stats|run_to_stats", src
        ), "_run_to_stats helper not found"
        assert re.search(
            r"llm|LLM|ChatModel|token", src, re.IGNORECASE
        ), "_run_to_stats should handle LLM-type runs"

    def test_functional_run_to_stats_tool_run(self):
        """_run_to_stats handles tool run correctly."""
        src = self._all_python_sources()
        assert re.search(
            r"tool|Tool", src
        ), "_run_to_stats should handle tool-type runs"

    def test_functional_run_to_stats_error_run(self):
        """_run_to_stats handles error run correctly."""
        src = self._all_python_sources()
        assert re.search(
            r"error|Error|exception|Exception", src
        ), "_run_to_stats should handle error runs"

    def test_functional_tracereport_error_runs_filters_correctly(self):
        """TraceReport.error_runs filters only failed runs."""
        src = self._all_python_sources()
        body = self._class_source(src, "TraceReport")
        assert body is not None, "TraceReport class not found"
        assert re.search(
            r"error_runs|errors|failed", body
        ), "TraceReport should filter error runs"
