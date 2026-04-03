"""
Test for 'similarity-search-patterns' skill — Milvus Similarity Search
Validates FilterBuilder chain, BatchSearch, TopK/Nprobe tuning,
index configuration, and search API patterns.
"""

import os
import re

import pytest


class TestSimilaritySearchPatterns:
    """Verify similarity search patterns in Milvus."""

    REPO_DIR = "/workspace/milvus"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_milvus_source_exists(self):
        """Verify Milvus source directory exists."""
        assert os.path.isdir(self.REPO_DIR), "Milvus repo not found"

    def test_search_related_files(self):
        """Verify search-related source files exist."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith((".go", ".py", ".cpp")) and "search" in f.lower():
                    found = True
                    break
            if found:
                break
        assert found, "No search-related files found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_filter_builder(self):
        """Verify FilterBuilder or filter chain pattern."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(FilterBuilder|filter.?builder|BoolExpr|bool_expr|filter_expr)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No FilterBuilder pattern found")

    def test_batch_search(self):
        """Verify BatchSearch capability."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(BatchSearch|batch_search|batch.?query|search_batch|hybrid.?search)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No BatchSearch found")

    def test_topk_parameter(self):
        """Verify TopK parameter in search API."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(r"(topk|top_k|TopK|limit\s*[:=])", content, re.IGNORECASE):
                return
        pytest.fail("No TopK parameter found")

    def test_nprobe_parameter(self):
        """Verify Nprobe or search parameter tuning."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(nprobe|Nprobe|search_param|ef\s*[:=]|nlist)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No Nprobe/search parameter found")

    def test_index_type_config(self):
        """Verify index type configuration (IVF_FLAT, HNSW, etc.)."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(IVF_FLAT|IVF_SQ8|HNSW|FLAT|ANNOY|IndexType)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No index type configuration found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_source_files_compile(self):
        """Verify Python source files compile (if any)."""
        import ast

        py_files = [f for f in self._find_source_files() if f.endswith(".py")]
        if not py_files:
            pytest.skip("No Python files to compile")
        for fpath in py_files[:10]:
            content = self._read(fpath)
            try:
                ast.parse(content, filename=fpath)
            except SyntaxError as e:
                pytest.fail(f"SyntaxError in {os.path.basename(fpath)}: {e}")

    def test_distance_metric(self):
        """Verify distance metric configuration (L2, IP, cosine)."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(metric_type|L2|InnerProduct|IP|cosine|MetricType)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No distance metric found")

    def test_collection_schema(self):
        """Verify collection schema definition."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(CollectionSchema|FieldSchema|create_collection|schema)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No collection schema found")

    def test_vector_dimension(self):
        """Verify vector dimension parameter."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(r"(dim\s*[:=]|dimension|vector_dim|DIM)", content):
                return
        pytest.fail("No vector dimension parameter found")

    def test_result_scoring(self):
        """Verify search results include scores/distances."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(score|distance|similarity|hits|SearchResult)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No result scoring found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_source_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith((".go", ".py", ".cpp", ".h", ".proto")):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
