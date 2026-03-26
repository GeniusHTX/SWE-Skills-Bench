"""
Test for 'python-performance-optimization' skill — Flame Graph Collapse Formatter
Validates that the Agent created a collapsed stack format output module
for py-spy in Rust, with filtering and CLI integration.
"""

import os
import re
import subprocess

import pytest


class TestPythonPerformanceOptimization:
    """Verify py-spy flamegraph_collapsed.rs module."""

    REPO_DIR = "/workspace/py-spy"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_flamegraph_collapsed_rs_exists(self):
        """src/flamegraph_collapsed.rs must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "src", "flamegraph_collapsed.rs")
        )

    def test_main_rs_references_module(self):
        """src/main.rs must reference the flamegraph_collapsed module."""
        content = self._read("src", "main.rs")
        patterns = [
            r"mod\s+flamegraph_collapsed",
            r"use.*flamegraph_collapsed",
            r"flamegraph_collapsed::",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "main.rs does not reference flamegraph_collapsed module"

    # ------------------------------------------------------------------
    # L1: Rust structure
    # ------------------------------------------------------------------

    def test_module_declares_functions(self):
        """flamegraph_collapsed.rs must declare at least one public function."""
        content = self._read("src", "flamegraph_collapsed.rs")
        assert re.search(
            r"pub\s+fn\s+\w+", content
        ), "No public functions in flamegraph_collapsed.rs"

    def test_module_has_struct_or_impl(self):
        """Module should define a struct or implement a trait."""
        content = self._read("src", "flamegraph_collapsed.rs")
        patterns = [r"pub\s+struct\s+\w+", r"impl\s+\w+", r"pub\s+trait\s+\w+"]
        assert any(
            re.search(p, content) for p in patterns
        ), "No struct/impl/trait found in flamegraph_collapsed.rs"

    # ------------------------------------------------------------------
    # L2: Collapsed format output
    # ------------------------------------------------------------------

    def test_generates_collapsed_format(self):
        """Module must produce collapsed stack format (func1;func2 count)."""
        content = self._read("src", "flamegraph_collapsed.rs")
        # Look for semicolon-separated stack joining and count output
        patterns = [
            r'";"\s*\.join',
            r"join.*\";\"",
            r"collapsed",
            r"stack.*count",
            r"write!.*\{.*\}.*\{",
            r"format!.*\{.*\}.*\{",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Module does not produce collapsed stack format"

    def test_aggregates_stacks(self):
        """Module must aggregate identical stacks and count samples."""
        content = self._read("src", "flamegraph_collapsed.rs")
        patterns = [
            r"HashMap",
            r"BTreeMap",
            r"counter",
            r"entry.*or_insert",
            r"\.count",
            r"aggregate",
            r"merge",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Module does not aggregate stacks"

    def test_includes_module_info_in_output(self):
        """Function names should include module/file information."""
        content = self._read("src", "flamegraph_collapsed.rs")
        patterns = [
            r"module",
            r"filename",
            r"file_name",
            r"file.*line",
            r"source",
            r"\.py",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Output does not include module/file information"

    # ------------------------------------------------------------------
    # L2: Filtering capabilities
    # ------------------------------------------------------------------

    def test_supports_min_sample_filter(self):
        """Module must support filtering by minimum sample count."""
        content = self._read("src", "flamegraph_collapsed.rs")
        patterns = [
            r"min.*count",
            r"minimum.*sample",
            r"threshold",
            r"min_samples",
            r"filter.*count",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Module does not support minimum sample count filter"

    def test_supports_exclusion_pattern(self):
        """Module must support excluding frames by pattern."""
        content = self._read("src", "flamegraph_collapsed.rs")
        patterns = [
            r"exclud",
            r"filter",
            r"pattern",
            r"regex",
            r"Regex",
            r"skip.*frame",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Module does not support frame exclusion patterns"

    def test_supports_top_n_limit(self):
        """Module must support limiting output to top N stacks."""
        content = self._read("src", "flamegraph_collapsed.rs")
        patterns = [
            r"top.*n",
            r"top_n",
            r"limit",
            r"max.*stacks",
            r"sort.*take",
            r"truncate",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Module does not support top-N limiting"

    # ------------------------------------------------------------------
    # L2: CLI integration
    # ------------------------------------------------------------------

    def test_main_adds_cli_option(self):
        """main.rs should add a CLI option for collapsed format."""
        content = self._read("src", "main.rs")
        patterns = [
            r"collapsed",
            r"flamegraph.*collapsed",
            r"format.*collapsed",
            r"output.*collapsed",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "main.rs does not add CLI option for collapsed format"
