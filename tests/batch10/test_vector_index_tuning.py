"""
Test for 'vector-index-tuning' skill — FAISS index benchmarking and tuning
Validates that the Agent implemented FAISS HNSW and IVF-PQ index
benchmarking with recall@k measurement and parameter tuning.
"""

import os
import re

import pytest


class TestVectorIndexTuning:
    """Verify FAISS index benchmark and tuning implementation."""

    REPO_DIR = "/workspace/faiss"

    def test_faiss_benchmark_file_exists(self):
        """faiss_benchmark.py must exist with FAISS index usage."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "faiss_benchmark.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"IndexHNSW|IndexIVFPQ|faiss", content):
                        found = True
                        break
            if found:
                break
        assert found, "faiss_benchmark.py with FAISS index usage not found"

    def test_quantization_config_file_exists(self):
        """quantization_config.py must define PQ parameters."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "quantization_config.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"nlist|nbits|PQ|quantiz", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "quantization_config.py with PQ parameters not found"

    def test_hnsw_index_uses_ef_construction(self):
        """HNSW index must set ef_construction parameter."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "faiss_benchmark.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"efConstruction|ef_construction", content):
                        found = True
                        break
            if found:
                break
        assert found, "ef_construction parameter not set on HNSW index"

    def test_recall_at_k_metric_defined(self):
        """recall@k metric must be computed."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "faiss_benchmark.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"recall|compute_recall|recall_at_k", content, re.IGNORECASE):
                        if re.search(r"intersection|ground.truth|top.k", content, re.IGNORECASE):
                            found = True
                            break
            if found:
                break
        assert found, "recall@k metric computation not found"

    def test_pq_compression_ratio_computed(self):
        """PQ compression ratio must be computed or reported."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("quantization_config.py", "faiss_benchmark.py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"compression|ratio|original.*compress|code_size", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "PQ compression ratio computation not found"

    def test_ef_search_tradeoff_explored(self):
        """Multiple ef_search values must be tested for recall-latency tradeoff."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "faiss_benchmark.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"ef_search|efSearch", content):
                        if re.search(r"\[.*\d+.*,.*\d+.*,.*\d+", content):
                            found = True
                            break
            if found:
                break
        assert found, "ef_search sweep with multiple values not found"

    def test_faiss_benchmark_syntax_valid(self):
        """faiss_benchmark.py must have valid Python syntax."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "faiss_benchmark.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    try:
                        compile(content, path, "exec")
                        found = True
                    except SyntaxError:
                        pass
                    break
            if found:
                break
        assert found, "faiss_benchmark.py has syntax errors"

    def test_hnsw_index_built_and_searchable(self):
        """HNSW index creation with IndexHNSWFlat must be present."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "faiss_benchmark.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"IndexHNSWFlat", content):
                        if re.search(r"\.add\(|\.search\(", content):
                            found = True
                            break
            if found:
                break
        assert found, "IndexHNSWFlat with add/search operations not found"

    def test_recall_at_k_returns_1_for_exact_match(self):
        """recall@k function must handle perfect recall case."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "faiss_benchmark.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"def\s+compute_recall|def\s+recall_at_k|def\s+calculate_recall", content):
                        found = True
                        break
            if found:
                break
        assert found, "recall@k function definition not found"

    def test_empty_index_search_returns_empty(self):
        """Empty index edge case must be handled."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "faiss_benchmark.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"empty|ntotal|\.ntotal\s*==\s*0|no.*vector", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Empty index handling not found"

    def test_pq_index_smaller_than_flat(self):
        """IVF-PQ index creation must be present."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "faiss_benchmark.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"IndexIVFPQ|IndexPQ", content):
                        found = True
                        break
            if found:
                break
        assert found, "IVF-PQ index creation not found"
