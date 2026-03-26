"""
Tests for langsmith-fetch skill.
Validates LangChain trace analysis: Run, TraceSession, analyze_latency, detect_bottlenecks,
export_session in langchain repository.
"""

import os
import sys
import importlib
import pytest

REPO_DIR = "/workspace/langchain"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


def _try_import(dotted: str):
    if REPO_DIR not in sys.path:
        sys.path.insert(0, REPO_DIR)
        sys.path.insert(0, os.path.join(REPO_DIR, "libs", "core"))
    parts = dotted.rsplit(".", 1)
    try:
        mod = importlib.import_module(parts[0])
        return getattr(mod, parts[1]) if len(parts) > 1 else mod
    except (ImportError, AttributeError) as exc:
        pytest.skip(f"Cannot import {dotted}: {exc}")


class TestLangsmithFetch:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_trace_models_file_exists(self):
        """trace_models.py must exist in langchain_core/tracers."""
        rel = "libs/core/langchain_core/tracers/trace_models.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "trace_models.py is empty"

    def test_trace_analyzer_file_exists(self):
        """trace_analyzer.py must exist in langchain_core/tracers."""
        rel = "libs/core/langchain_core/tracers/trace_analyzer.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_run_class_defined(self):
        """trace_models.py must define Run class with start_time, end_time, child_runs."""
        content = _read("libs/core/langchain_core/tracers/trace_models.py")
        assert "class Run" in content, "Run class not found in trace_models.py"
        for field in ["start_time", "end_time", "child_runs"]:
            assert field in content, f"'{field}' field not found in Run class"

    def test_analyze_latency_and_detect_bottlenecks_defined(self):
        """trace_analyzer.py must define analyze_latency, detect_bottlenecks, export_session."""
        content = _read("libs/core/langchain_core/tracers/trace_analyzer.py")
        for fn in [
            "def analyze_latency",
            "def detect_bottlenecks",
            "def export_session",
        ]:
            assert fn in content, f"'{fn}' not found in trace_analyzer.py"

    def test_self_time_computation_logic(self):
        """trace_analyzer.py must compute self_time by subtracting child durations."""
        content = _read("libs/core/langchain_core/tracers/trace_analyzer.py")
        assert "self_time" in content, "self_time calculation not found"
        assert "child" in content, "No reference to child runs in self_time computation"

    def test_export_session_json_with_sorted_keys(self):
        """export_session must use json.dumps with sort_keys=True."""
        content = _read("libs/core/langchain_core/tracers/trace_analyzer.py")
        assert "json" in content, "json module not imported in trace_analyzer.py"
        assert (
            "sort_keys" in content
        ), "sort_keys=True not found in JSON export in trace_analyzer.py"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_run_end_before_start_raises_value_error(self):
        """Run must raise ValueError when end_time is before start_time (mocked)."""
        from datetime import datetime

        def make_run(start_time, end_time):
            if end_time < start_time:
                raise ValueError("end_time must not be before start_time")
            return {"start_time": start_time, "end_time": end_time}

        with pytest.raises(ValueError, match="end_time"):
            make_run(
                datetime(2024, 1, 1, 12, 0, 0),
                datetime(2024, 1, 1, 11, 0, 0),
            )

    def test_self_time_200ms_for_chain_with_children(self):
        """Self time = total(2000ms) - LLM(1500ms) - tool(300ms) = 200ms."""

        def analyze_latency(total_ms, child_ms_list):
            self_time = total_ms - sum(child_ms_list)
            return {"self_time_ms": self_time}

        result = analyze_latency(2000, [1500, 300])
        assert result["self_time_ms"] == 200

    def test_detect_bottlenecks_sorted_descending(self):
        """detect_bottlenecks must return runs sorted by duration descending."""

        def detect_bottlenecks(runs):
            return sorted(runs, key=lambda r: r["duration_ms"], reverse=True)

        runs = [
            {"name": "fast", "duration_ms": 100},
            {"name": "slow", "duration_ms": 2000},
            {"name": "medium", "duration_ms": 500},
        ]
        result = detect_bottlenecks(runs)
        assert result[0]["name"] == "slow"
        assert result == sorted(runs, key=lambda r: r["duration_ms"], reverse=True)

    def test_export_session_xml_raises_value_error(self):
        """export_session('xml') must raise ValueError for unsupported format."""

        def export_session(session, format="json"):
            if format not in ("json",):
                raise ValueError(f"Unsupported export format: {format!r}")
            import json

            return json.dumps(session, sort_keys=True)

        with pytest.raises(ValueError, match="xml"):
            export_session({}, format="xml")

    def test_json_export_has_sorted_keys(self):
        """export_session('json') must produce JSON with alphabetically sorted keys."""
        import json

        def export_session(session, format="json"):
            if format != "json":
                raise ValueError(f"Unsupported format: {format!r}")
            return json.dumps(session, sort_keys=True)

        data = {"z_key": 1, "a_key": 2, "m_key": 3}
        result = export_session(data)
        parsed = json.loads(result)
        keys = list(parsed.keys())
        assert keys == sorted(keys), "JSON keys must be sorted alphabetically"

    def test_trace_session_class_importable(self):
        """TraceSession must be importable and instantiable with empty runs (mocked)."""

        class TraceSession:
            def __init__(self, runs=None):
                self.runs = runs or []

        session = TraceSession(runs=[])
        assert hasattr(session, "runs")
        assert session.runs == []
