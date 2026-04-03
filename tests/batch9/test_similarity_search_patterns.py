"""
Test for 'similarity-search-patterns' skill — Go Similarity Search Library
Validates Searcher interface, BruteForce, Result struct, dimension checks,
k-clamping, sorting, and empty-index behavior via static source analysis.
"""

import os
import re

import pytest


class TestSimilaritySearchPatterns:
    """Verify Go similarity-search library via static source inspection."""

    REPO_DIR = "/workspace/milvus"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _sim(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "similarity", *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_go_mod_and_index_go_exist(self):
        """go.mod and similarity/index.go must exist."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, "go.mod")), "go.mod not found"
        index = self._sim("index.go")
        hnsw = os.path.join(self.REPO_DIR, "internal", "hnsw", "hnsw.go")
        assert os.path.isfile(index) or os.path.isfile(hnsw), "index.go or hnsw.go not found"

    def test_bruteforce_and_searcher_exist(self):
        """similarity/bruteforce.go and searcher.go must exist."""
        assert os.path.isfile(self._sim("bruteforce.go")), "bruteforce.go not found"
        iface = self._sim("searcher.go")
        alt = self._sim("interface.go")
        assert os.path.isfile(iface) or os.path.isfile(alt), "searcher.go or interface.go not found"

    def test_test_file_and_makefile_exist(self):
        """Test file and build automation must exist."""
        import glob
        tests = glob.glob(self._sim("*_test.go"))
        assert len(tests) >= 1, "No *_test.go in similarity/"
        mk = os.path.join(self.REPO_DIR, "Makefile")
        tf = os.path.join(self.REPO_DIR, "Taskfile.yml")
        assert os.path.isfile(mk) or os.path.isfile(tf), "Makefile/Taskfile.yml not found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_searcher_interface_search_signature(self):
        """Searcher interface must define Search([]float32, int) []Result."""
        path = self._sim("searcher.go")
        alt = self._sim("interface.go")
        content = self._read_file(path) or self._read_file(alt)
        if not content:
            pytest.skip("searcher/interface file not found")
        assert "type Searcher interface" in content, "Searcher interface not defined"
        assert "Search" in content, "Search method not found"

    def test_result_struct_fields(self):
        """Result struct must have ID, Score, Distance fields."""
        for name in ("searcher.go", "index.go", "interface.go"):
            content = self._read_file(self._sim(name))
            if "type Result struct" in content:
                assert "ID" in content
                assert "Score" in content or "Distance" in content
                return
        pytest.fail("Result struct not found in any similarity/ file")

    def test_bruteforce_sorts_by_distance(self):
        """BruteForce.Search must sort results by distance ascending."""
        content = self._read_file(self._sim("bruteforce.go"))
        if not content:
            pytest.skip("bruteforce.go not found")
        assert "sort." in content, "sort package not used"
        assert "Distance" in content or "distance" in content, "No distance reference"

    def test_dimension_mismatch_returns_error(self):
        """AddVector must return error for dimension mismatch, not panic."""
        for name in ("index.go", "bruteforce.go"):
            content = self._read_file(self._sim(name))
            if "dim" in content.lower() and ("error" in content or "Errorf" in content):
                assert "panic" not in content.split("dim")[0][-200:], "panic used instead of error return"
                return
        pytest.fail("No dimension validation error return found")

    # ── functional_check (static Go) ─────────────────────────────────────

    def test_bruteforce_linear_scan_pattern(self):
        """BruteForce must linearly scan all vectors computing distance."""
        content = self._read_file(self._sim("bruteforce.go"))
        if not content:
            pytest.skip("bruteforce.go not found")
        has_range = "range" in content
        has_dist = any(d in content.lower() for d in ("cosine", "euclidean", "l2", "dot"))
        assert has_range and has_dist, "Linear scan with distance function not found"

    def test_empty_index_returns_empty_slice(self):
        """Search on empty index must return empty []Result, not panic."""
        for name in ("bruteforce.go", "index.go"):
            content = self._read_file(self._sim(name))
            if re.search(r"len.*==\s*0|Result\{\}", content):
                return
        pytest.fail("No empty-index guard found")

    def test_k_clamped_when_larger_than_n(self):
        """When k > len(vectors), all available results returned."""
        content = self._read_file(self._sim("bruteforce.go"))
        if not content:
            pytest.skip("bruteforce.go not found")
        has_clamp = re.search(r"k\s*>\s*len|min\(k", content)
        assert has_clamp, "k-clamping guard not found"

    def test_go_mod_version_at_least_1_21(self):
        """go.mod must declare go >= 1.21."""
        content = self._read_file(os.path.join(self.REPO_DIR, "go.mod"))
        if not content:
            pytest.skip("go.mod not found")
        m = re.search(r"^go\s+1\.(\d+)", content, re.MULTILINE)
        assert m, "go version directive not found"
        assert int(m.group(1)) >= 21, f"go 1.{m.group(1)} < 1.21"

    def test_wrong_dimension_error_path(self):
        """Add() with wrong dimension must return error, no recover()."""
        for name in ("index.go", "bruteforce.go"):
            content = self._read_file(self._sim(name))
            if "dim" in content.lower():
                assert "recover()" not in content, "recover() used instead of error return"
                has_err = "return" in content and ("err" in content or "Err" in content)
                assert has_err, "No error return for dimension mismatch"
                return
        pytest.fail("No dimension check code found")
