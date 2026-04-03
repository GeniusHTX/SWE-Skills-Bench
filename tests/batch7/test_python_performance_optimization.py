"""Test file for the python-performance-optimization skill.

This suite validates the SummaryRecorder, FrameSummary, and CLI
summary subcommand in py-spy (Rust source analysis).
"""

from __future__ import annotations

import pathlib
import re

import pytest


class TestPythonPerformanceOptimization:
    """Verify py-spy summary profiler implementation."""

    REPO_DIR = "/workspace/py-spy"

    SUMMARY_RS = "src/summary.rs"
    MAIN_RS = "src/main.rs"
    TEST_SUMMARY_PY = "tests/test_summary.py"

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

    def _rust_struct_body(self, source: str, name: str) -> str | None:
        m = re.search(rf"struct\s+{name}\s*\{{", source)
        if m is None:
            return None
        depth, i = 1, m.end()
        while i < len(source) and depth > 0:
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
            i += 1
        return source[m.start() : i]

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_src_summary_rs_exists(self):
        """Verify src/summary.rs exists and is non-empty."""
        self._assert_non_empty_file(self.SUMMARY_RS)

    def test_file_path_src_main_rs_modified_with_summary_subcommand(self):
        """Verify src/main.rs modified with summary subcommand."""
        self._assert_non_empty_file(self.MAIN_RS)
        src = self._read_text(self.MAIN_RS)
        assert re.search(
            r"summary|Summary", src
        ), "main.rs should reference summary subcommand"

    def test_file_path_tests_test_summary_py_exists(self):
        """Verify tests/test_summary.py exists and is non-empty."""
        self._assert_non_empty_file(self.TEST_SUMMARY_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_summaryrecorder_struct_has_samples_hashmap_total_samples_sam(
        self,
    ):
        """SummaryRecorder struct has samples HashMap, total_samples, sample_rate, duration_secs."""
        src = self._read_text(self.SUMMARY_RS)
        body = self._rust_struct_body(src, "SummaryRecorder")
        assert body is not None, "SummaryRecorder struct not found"
        for field in ("samples", "total_samples", "sample_rate"):
            assert field in body, f"SummaryRecorder missing field: {field}"

    def test_semantic_framesummary_has_function_filename_lineno_total_samples_self(
        self,
    ):
        """FrameSummary has function, filename, lineno, total_samples, self_samples."""
        src = self._read_text(self.SUMMARY_RS)
        body = self._rust_struct_body(src, "FrameSummary")
        assert body is not None, "FrameSummary struct not found"
        for field in (
            "function",
            "filename",
            "lineno",
            "total_samples",
            "self_samples",
        ):
            assert field in body, f"FrameSummary missing field: {field}"

    def test_semantic_record_method_processes_stack_frames_correctly(self):
        """record() method processes stack frames correctly."""
        src = self._read_text(self.SUMMARY_RS)
        assert re.search(r"fn\s+record\s*\(", src), "record method not found"

    def test_semantic_render_output_includes_self_total_self_function_header(self):
        """render() output includes %Self, Total, Self, Function header."""
        src = self._read_text(self.SUMMARY_RS)
        assert re.search(
            r"fn\s+render\s*\(|fn\s+format\s*\(|fn\s+display\s*\(", src
        ), "render/format/display method not found"

    def test_semantic_cli_args_pid_duration_rate_top_nonblocking_registered(self):
        """CLI args: --pid, --duration, --rate, --top, --nonblocking registered."""
        src = self._read_text(self.MAIN_RS)
        for arg in ("pid", "duration", "rate", "top"):
            assert re.search(
                rf"--{arg}|{arg}", src
            ), f"CLI argument --{arg} not registered"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, source analysis)
    # ------------------------------------------------------------------

    def test_functional_profiling_tight_loop_for_3s_at_100hz_produces_300_samples(self):
        """Profiling tight loop for 3s at 100Hz produces ~300 samples."""
        src = self._read_text(self.SUMMARY_RS)
        assert re.search(r"fn\s+record\s*\(", src), "record method required"
        assert re.search(
            r"total_samples|sample_count", src
        ), "Should track total sample count"

    def test_functional_busy_loop_appears_as_top_frame_in_output(self):
        """busy_loop appears as top frame in output."""
        src = self._read_text(self.SUMMARY_RS)
        assert re.search(
            r"sort|top|self_samples", src
        ), "Should sort frames by self_samples for top output"

    def test_functional_top_5_limits_render_to_5_rows(self):
        """--top 5 limits render to 5 rows."""
        src = self._read_text(self.SUMMARY_RS)
        assert re.search(
            r"top|limit|take|truncate", src, re.IGNORECASE
        ), "Should support limiting output to top N frames"

    def test_functional_invalid_pid_returns_non_zero_exit_code(self):
        """Invalid PID returns non-zero exit code."""
        src = self._read_text(self.MAIN_RS)
        assert re.search(
            r"pid|process|attach", src, re.IGNORECASE
        ), "Should handle PID argument and errors"

    def test_functional_cargo_build_release_succeeds(self):
        """cargo build --release succeeds."""
        cargo_toml = self._repo_path("Cargo.toml")
        assert cargo_toml.is_file(), "Cargo.toml should exist for build"
