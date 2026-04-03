"""
Test for 'vector-index-tuning' skill — FAISS Vector Index Tuning
Validates 5 index types, recall@k evaluation, perf_counter timing,
index configuration, and search quality measurement.
"""

import os
import re

import pytest


class TestVectorIndexTuning:
    """Verify FAISS vector index tuning patterns."""

    REPO_DIR = "/workspace/faiss"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_faiss_source_exists(self):
        """Verify FAISS source directory exists."""
        assert os.path.isdir(self.REPO_DIR), "FAISS repo not found"

    def test_index_source_files(self):
        """Verify index-related source files exist."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith((".py", ".cpp", ".h")) and "index" in f.lower():
                    found = True
                    break
            if found:
                break
        assert found, "No index source files found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_five_index_types(self):
        """Verify at least 5 index types are referenced."""
        source_files = self._find_source_files()
        index_types = set()
        patterns = [
            r"IndexFlat",
            r"IndexIVFFlat",
            r"IndexIVFPQ",
            r"IndexHNSW",
            r"IndexLSH",
            r"IndexPQ",
            r"IndexIVFScalar",
            r"IndexScalar",
            r"GpuIndex",
            r"IndexBinary",
            r"IndexIVF",
        ]
        for fpath in source_files:
            content = self._read(fpath)
            for pat in patterns:
                if re.search(pat, content):
                    index_types.add(pat.replace(r"\\", ""))
        assert (
            len(index_types) >= 5
        ), f"Only {len(index_types)} index types found: {index_types}"

    def test_recall_at_k(self):
        """Verify recall@k evaluation metric."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(recall|recall@|recall_at_k|intersection|groundtruth)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No recall@k evaluation found")

    def test_perf_counter_timing(self):
        """Verify perf_counter or timing measurement."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(perf_counter|time\.time|timeit|elapsed|duration|chrono)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No timing measurement found")

    def test_nprobe_parameter(self):
        """Verify nprobe parameter for IVF indices."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(r"(nprobe|n_probe)", content, re.IGNORECASE):
                return
        pytest.fail("No nprobe parameter found")

    def test_training_data(self):
        """Verify index training with data."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(\.train\(|training|train_data|is_trained)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No index training found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_python_files_parse(self):
        """Verify Python files parse correctly."""
        import ast

        py_files = [f for f in self._find_source_files() if f.endswith(".py")]
        for fpath in py_files[:15]:
            content = self._read(fpath)
            try:
                ast.parse(content, filename=fpath)
            except SyntaxError as e:
                pytest.fail(f"SyntaxError in {os.path.basename(fpath)}: {e}")

    def test_search_api(self):
        """Verify search API (index.search)."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(r"(\.search\(|range_search|search_with_params)", content):
                return
        pytest.fail("No search API found")

    def test_add_vectors(self):
        """Verify adding vectors to index."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(r"(\.add\(|add_with_ids|ntotal)", content):
                return
        pytest.fail("No vector adding found")

    def test_index_io(self):
        """Verify index save/load (write_index/read_index)."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(write_index|read_index|save_index|load_index|serialize)", content
            ):
                return
        pytest.fail("No index I/O found")

    def test_dimension_parameter(self):
        """Verify dimension parameter for index creation."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(r"(d\s*=\s*\d+|dim\s*=|dimension|d_model)", content):
                return
        pytest.fail("No dimension parameter found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_source_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith((".py", ".cpp", ".h", ".cuh")):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
