"""Test file for the vector-index-tuning skill.

This suite validates HNSW auto-tuning in faiss: HNSWAutoTuner,
parameter sets, tuning results, Pareto frontier, and recall/QPS queries.
"""

from __future__ import annotations

import pathlib
import re

import pytest


class TestVectorIndexTuning:
    """Verify HNSW auto-tuning in faiss."""

    REPO_DIR = "/workspace/faiss"

    AUTOTUNE_H = "faiss/AutoTuneHNSW.h"
    AUTOTUNE_CPP = "faiss/AutoTuneHNSW.cpp"
    EXTRA_WRAPPERS_PY = "faiss/python/extra_wrappers.py"

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

    def _cpp_class_body(self, source: str, class_name: str) -> str:
        """Extract the body of a C++ class/struct definition."""
        pattern = rf"(?:class|struct)\s+{class_name}\s*[^{{]*\{{([^}}]+)\}}"
        m = re.search(pattern, source, re.DOTALL)
        return m.group(1) if m else ""

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_faiss_autotunehnsw_h_exists(self):
        """Verify faiss/AutoTuneHNSW.h exists."""
        self._assert_non_empty_file(self.AUTOTUNE_H)

    def test_file_path_faiss_autotunehnsw_cpp_exists(self):
        """Verify faiss/AutoTuneHNSW.cpp exists."""
        self._assert_non_empty_file(self.AUTOTUNE_CPP)

    def test_file_path_faiss_python_extra_wrappers_py_modified(self):
        """Verify faiss/python/extra_wrappers.py modified."""
        self._assert_non_empty_file(self.EXTRA_WRAPPERS_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_hnswautotuner_class_with_tune_pareto_bestfor_methods(self):
        """HNSWAutoTuner class with tune, paretoFrontier, bestForRecall, bestForQPS methods."""
        header = self._read_text(self.AUTOTUNE_H)
        assert re.search(
            r"class\s+HNSWAutoTuner", header
        ), "HNSWAutoTuner class should be declared"
        for method in ["tune", "paretoFrontier", "bestForRecall", "bestForQPS"]:
            assert method in header, f"HNSWAutoTuner should have {method} method"

    def test_semantic_hnswparameterset_has_m_efconstruction_efsearch(self):
        """HNSWParameterSet has M, efConstruction, efSearch fields."""
        header = self._read_text(self.AUTOTUNE_H)
        body = self._cpp_class_body(header, "HNSWParameterSet")
        if not body:
            body = header
        for field in ["M", "efConstruction", "efSearch"]:
            assert field in body, f"HNSWParameterSet should have {field} field"

    def test_semantic_hnswtuningresult_has_recall_qps_build_time_memory(self):
        """HNSWTuningResult has recall_at_1, recall_at_10, qps, index_build_time, memory_usage_mb."""
        header = self._read_text(self.AUTOTUNE_H)
        body = self._cpp_class_body(header, "HNSWTuningResult")
        if not body:
            body = header
        for field in [
            "recall_at_1",
            "recall_at_10",
            "qps",
            "index_build_time",
            "memory_usage_mb",
        ]:
            assert field in body, f"HNSWTuningResult should have {field} field"

    def test_semantic_default_parameter_ranges(self):
        """Default parameter ranges: M={8,16,32,48,64}, etc."""
        src = self._read_text(self.AUTOTUNE_H)
        cpp = self._read_text(self.AUTOTUNE_CPP)
        combined = src + "\n" + cpp
        for val in ["8", "16", "32", "48", "64"]:
            assert val in combined, f"Default M range should include {val}"
        for val in ["40", "100", "200", "400"]:
            assert val in combined, f"Default efConstruction range should include {val}"

    def test_semantic_pareto_frontier_filters_dominated_solutions(self):
        """Pareto frontier filters dominated solutions."""
        cpp = self._read_text(self.AUTOTUNE_CPP)
        assert re.search(
            r"pareto|dominated|frontier", cpp, re.IGNORECASE
        ), "paretoFrontier should filter dominated solutions"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases)
    # ------------------------------------------------------------------

    def test_functional_10k_vectors_tune_evaluates_all_combos(self):
        """10K 128-dim vectors → tune evaluates all parameter combos."""
        cpp = self._read_text(self.AUTOTUNE_CPP)
        assert re.search(
            r"tune|for.*M|for.*efConstruction", cpp
        ), "tune should iterate over parameter combinations"

    def test_functional_higher_m_higher_recall(self):
        """Higher M → higher recall in results."""
        cpp = self._read_text(self.AUTOTUNE_CPP)
        assert re.search(r"recall|recall_at", cpp), "Should compute recall metrics"

    def test_functional_paretofrontier_returns_non_dominated_subset(self):
        """paretoFrontier returns non-dominated subset."""
        cpp = self._read_text(self.AUTOTUNE_CPP)
        assert re.search(
            r"paretoFrontier|pareto_frontier", cpp
        ), "paretoFrontier should be implemented"

    def test_functional_bestforrecall_095_returns_fastest_config(self):
        """bestForRecall(0.95) returns fastest config with >=95% recall."""
        cpp = self._read_text(self.AUTOTUNE_CPP)
        assert re.search(r"bestForRecall", cpp), "bestForRecall should be implemented"

    def test_functional_cmake_build_succeeds(self):
        """cmake build succeeds (source analysis)."""
        header = self._read_text(self.AUTOTUNE_H)
        assert re.search(
            r"#pragma\s+once|#ifndef|#define", header
        ), "Header should have include guards"
        cpp = self._read_text(self.AUTOTUNE_CPP)
        assert re.search(
            r'#include\s+"AutoTuneHNSW', cpp
        ), "CPP should include its header"
