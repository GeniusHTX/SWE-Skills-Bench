"""
Test for 'vector-index-tuning' skill — FAISS HNSW Tuner & Quantization Advisor
Validates that the Agent created HNSWTuner and QuantizationAdvisor with
benchmark and recommend methods in the FAISS contrib directory.
"""

import ast
import os
import sys

import pytest


class TestVectorIndexTuning:
    """Verify HNSW tuner and quantization advisor in FAISS."""

    REPO_DIR = "/workspace/faiss"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _tuner_tree(self):
        text = self._read(os.path.join(self.REPO_DIR, "contrib/hnsw_tuner.py"))
        return ast.parse(text)

    def _classes(self):
        tree = self._tuner_tree()
        return [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

    def _methods(self):
        tree = self._tuner_tree()
        return [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]

    # ---- file_path_check ----

    def test_hnsw_tuner_exists(self):
        """Verifies contrib/hnsw_tuner.py exists."""
        path = os.path.join(self.REPO_DIR, "contrib/hnsw_tuner.py")
        assert os.path.exists(path), f"File not found: {path}"

    def test_quantization_advisor_exists(self):
        """Verifies contrib/quantization_advisor.py exists."""
        path = os.path.join(self.REPO_DIR, "contrib/quantization_advisor.py")
        assert os.path.exists(path), f"File not found: {path}"

    def test_test_file_exists(self):
        """Verifies tests/test_hnsw_tuner.py exists."""
        path = os.path.join(self.REPO_DIR, "tests/test_hnsw_tuner.py")
        assert os.path.exists(path), f"File not found: {path}"

    # ---- semantic_check ----

    def test_sem_ast_parseable(self):
        """Verifies hnsw_tuner.py is valid Python."""
        tree = self._tuner_tree()
        assert tree is not None

    def test_sem_hnsw_tuner_class(self):
        """Verifies HNSWTuner class is defined."""
        assert "HNSWTuner" in self._classes(), "HNSWTuner class not defined"

    def test_sem_benchmark_method(self):
        """Verifies benchmark method exists."""
        assert "benchmark" in self._methods(), "benchmark method missing"

    def test_sem_recommend_method(self):
        """Verifies recommend method exists."""
        assert "recommend" in self._methods(), "recommend method missing"

    def test_sem_classes_list(self):
        """Verifies classes found via AST."""
        classes = self._classes()
        assert len(classes) >= 1, "No classes found in hnsw_tuner.py"

    def test_sem_methods_list(self):
        """Verifies methods found via AST (edge case)."""
        methods = self._methods()
        assert len(methods) >= 2, f"Expected >= 2 methods, found {len(methods)}"

    # ---- functional_check ----

    def test_func_import_hnsw_tuner(self):
        """Verifies HNSWTuner is importable from contrib."""
        old_path = sys.path[:]
        sys.path.insert(0, os.path.join(self.REPO_DIR, "contrib"))
        try:
            from hnsw_tuner import HNSWTuner  # type: ignore

            assert HNSWTuner is not None
        finally:
            sys.path[:] = old_path

    def test_func_import_quantization_advisor(self):
        """Verifies QuantizationAdvisor is importable."""
        old_path = sys.path[:]
        sys.path.insert(0, os.path.join(self.REPO_DIR, "contrib"))
        try:
            from quantization_advisor import QuantizationAdvisor  # type: ignore

            assert QuantizationAdvisor is not None
        finally:
            sys.path[:] = old_path

    def test_func_test_params(self):
        """Verifies n, d, k = 500, 32, 5 pattern in test file."""
        test_text = self._read(os.path.join(self.REPO_DIR, "tests/test_hnsw_tuner.py"))
        assert "500" in test_text, "n=500 not in test file"
        assert "32" in test_text, "d=32 not in test file"

    def test_func_rng_pattern(self):
        """Verifies np.random.default_rng usage."""
        test_text = self._read(os.path.join(self.REPO_DIR, "tests/test_hnsw_tuner.py"))
        assert "default_rng" in test_text, "default_rng pattern not found"

    def test_func_float32_vectors(self):
        """Verifies float32 vector generation."""
        test_text = self._read(os.path.join(self.REPO_DIR, "tests/test_hnsw_tuner.py"))
        assert "float32" in test_text, "float32 dtype not found in tests"

    def test_func_faiss_import_in_test(self):
        """Verifies faiss import in test file."""
        test_text = self._read(os.path.join(self.REPO_DIR, "tests/test_hnsw_tuner.py"))
        assert (
            "import faiss" in test_text or "faiss" in test_text
        ), "faiss not imported in test"

    def test_func_index_search(self):
        """Verifies index.search usage pattern."""
        test_text = self._read(os.path.join(self.REPO_DIR, "tests/test_hnsw_tuner.py"))
        assert "search" in test_text, "index.search pattern not found"

    def test_func_shape_mismatch_handling(self):
        """Failure case: ground_truth shape mismatch -> ValueError."""
        tuner_text = self._read(os.path.join(self.REPO_DIR, "contrib/hnsw_tuner.py"))
        assert (
            "ValueError" in tuner_text or "shape" in tuner_text
        ), "No shape mismatch handling found"

    def test_func_query_vectors(self):
        """Verifies query vector generation in test."""
        test_text = self._read(os.path.join(self.REPO_DIR, "tests/test_hnsw_tuner.py"))
        assert (
            "queries" in test_text or "query" in test_text
        ), "No query vectors in test"
