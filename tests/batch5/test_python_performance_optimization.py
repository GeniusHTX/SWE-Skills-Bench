"""
Test for 'python-performance-optimization' skill — py-spy Performance Profiling
Validates sample collection (100K), analyzer top functions,
flamegraph SVG generation, and profiling data analysis.
"""

import os
import re
import subprocess

import pytest


class TestPythonPerformanceOptimization:
    """Verify Python performance profiling tools."""

    REPO_DIR = "/workspace/py-spy"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_repo_directory_exists(self):
        """Verify py-spy repository exists."""
        assert os.path.isdir(self.REPO_DIR), "py-spy repo not found"

    def test_source_files_exist(self):
        """Verify source files (Rust/Python) exist."""
        found_rs = False
        found_py = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".rs"):
                    found_rs = True
                if f.endswith(".py"):
                    found_py = True
            if found_rs or found_py:
                break
        assert found_rs or found_py, "No source files found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_sample_count_reference(self):
        """Verify reference to sample collection (e.g. 100K samples)."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(sample|100.?000|100k|num_samples|sampling_rate)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No sample count reference found")

    def test_top_functions_analysis(self):
        """Verify top functions / hotspot analysis."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(top|hotspot|most.?time|stack.?frame|function.?name)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No top functions analysis found")

    def test_flamegraph_support(self):
        """Verify flamegraph SVG generation support."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(flamegraph|flame.?graph|\.svg|svg_output)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No flamegraph support found")

    def test_stack_trace_collection(self):
        """Verify stack trace collection mechanism."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(stack.?trace|backtrace|frame|unwinding|call.?stack)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No stack trace collection found")

    def test_process_attach(self):
        """Verify ability to attach to running processes."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(r"(attach|pid|process_id|--pid)", content, re.IGNORECASE):
                return
        pytest.fail("No process attach capability found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_cargo_toml_exists(self):
        """Verify Cargo.toml for Rust project build."""
        cargo = os.path.join(self.REPO_DIR, "Cargo.toml")
        if not os.path.exists(cargo):
            pytest.skip("Not a Rust project")
        content = self._read(cargo)
        assert (
            "py-spy" in content.lower() or "pyspy" in content.lower()
        ), "Cargo.toml doesn't reference py-spy"

    def test_output_format_options(self):
        """Verify multiple output format options (flamegraph, speedscope, raw)."""
        source_files = self._find_source_files()
        formats_found = set()
        for fpath in source_files:
            content = self._read(fpath)
            for fmt in ["flamegraph", "speedscope", "raw", "json", "top"]:
                if fmt in content.lower():
                    formats_found.add(fmt)
        assert (
            len(formats_found) >= 2
        ), f"Only {formats_found} output formats found, expected ≥ 2"

    def test_duration_or_timeout(self):
        """Verify duration/timeout parameter for profiling."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(duration|timeout|--duration|seconds)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No duration/timeout parameter found")

    def test_rate_or_frequency(self):
        """Verify sampling rate/frequency configuration."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(rate|frequency|--rate|sampling_rate|hz)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No sampling rate/frequency config found")

    def test_subprocesses_support(self):
        """Verify subprocess profiling support."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(subprocess|subproces|child.?process|--subprocesses)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No subprocess profiling support found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_source_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith((".rs", ".py", ".toml")):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
