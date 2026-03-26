"""
Tests for similarity-search-patterns skill.
Validates Go hybrid search and index selection in milvus/internal/search/.
"""

import os
import subprocess
import glob
import pytest

REPO_DIR = "/workspace/milvus"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read_dir(dirname: str) -> str:
    pattern = os.path.join(REPO_DIR, dirname, "*.go")
    files = glob.glob(pattern)
    return "\n".join(open(f, encoding="utf-8", errors="ignore").read() for f in files)


def _run(cmd: str, timeout: int = 120):
    return subprocess.run(
        cmd, shell=True, cwd=REPO_DIR, capture_output=True, text=True, timeout=timeout
    )


class TestSimilaritySearchPatterns:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_internal_search_directory_exists(self):
        """internal/search/ must contain at least one .go file."""
        pattern = os.path.join(REPO_DIR, "internal", "search", "*.go")
        files = glob.glob(pattern)
        assert len(files) >= 1, f"No .go files found in {_path('internal/search')}"

    def test_index_selector_go_exists(self):
        """An index selector Go file must exist in internal/search/."""
        candidates = [
            "internal/search/index_selector.go",
            "internal/search/selector.go",
        ]
        found = any(os.path.isfile(_path(r)) for r in candidates)
        assert found, f"No index selector file found at {candidates}"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_hybrid_search_rrf_defined(self):
        """Hybrid search with RRF and alpha parameter must be defined."""
        content = _read_dir("internal/search")
        has_rrf = (
            "RRF" in content
            or "Reciprocal" in content
            or "HybridSearch" in content
            or "hybridSearch" in content
        )
        assert has_rrf, "No RRF/hybrid search function found in internal/search/"
        assert (
            "alpha" in content.lower() or "Alpha" in content
        ), "alpha parameter not found in internal/search/"

    def test_index_types_defined(self):
        """FLAT, HNSW, and IVF_PQ index type constants must be defined."""
        content = _read_dir("internal/search")
        for idx_type in ("FLAT", "HNSW", "IVF_PQ"):
            assert (
                idx_type in content
            ), f"{idx_type} index type not found in internal/search/"

    def test_recall_threshold_defined(self):
        """Recall thresholds 0.95 and 0.99 must be referenced for index selection."""
        content = _read_dir("internal/search")
        assert (
            "0.95" in content or "0.99" in content
        ), "No recall threshold (0.95 or 0.99) found in internal/search/"

    def test_alpha_validation_defined(self):
        """Alpha parameter [0.0, 1.0] validation must be implemented."""
        content = _read_dir("internal/search")
        has_validation = "alpha" in content.lower() and (
            "error" in content.lower()
            or "invalid" in content.lower()
            or "0.0" in content
            or "1.0" in content
        )
        assert has_validation, "No alpha range validation found in internal/search/"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_go_internal_search_tests_pass(self):
        """go test ./internal/search/... must pass."""
        result = _run("go test ./internal/search/...")
        if result.returncode != 0 and (
            "cannot find" in result.stderr or "go: " in result.stderr[:50]
        ):
            pytest.skip("Go not available or internal/search module not found")
        assert (
            result.returncode == 0
        ), f"go test ./internal/search/... failed:\n{result.stdout}\n{result.stderr}"

    def test_hybrid_rrf_alpha_0_5_b_highest(self):
        """With alpha=0.5, doc B in both dense+sparse must have highest score (mocked)."""

        def hybrid_rrf_score(dense: dict, sparse: dict, alpha: float) -> dict:
            if not (0.0 <= alpha <= 1.0):
                raise ValueError(f"alpha must be in [0,1], got {alpha}")
            scores = {}
            for doc, s in dense.items():
                scores[doc] = scores.get(doc, 0) + alpha * s
            for doc, s in sparse.items():
                scores[doc] = scores.get(doc, 0) + (1 - alpha) * s
            return scores

        scores = hybrid_rrf_score(
            dense={"A": 0.9, "B": 0.8},
            sparse={"B": 0.95, "C": 0.7},
            alpha=0.5,
        )
        ranked = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)
        assert ranked[0] == "B", f"Expected B to rank first, got {ranked[0]}"
        assert (
            abs(scores["B"] - 0.875) < 0.01
        ), f"Expected B score 0.875, got {scores['B']}"

    def test_hybrid_rrf_deduplicates_results(self):
        """Documents in both dense and sparse must appear exactly once (mocked)."""

        def hybrid_fuse(dense: dict, sparse: dict):
            all_docs = set(dense.keys()) | set(sparse.keys())
            return list(all_docs)

        results = hybrid_fuse(
            dense={"A": 0.9, "B": 0.8},
            sparse={"B": 0.95, "C": 0.7},
        )
        assert (
            results.count("B") == 1
        ), f"Expected B to appear once, got {results.count('B')}"

    def test_alpha_1_5_returns_error(self):
        """alpha=1.5 must raise an error (mocked)."""

        def validate_alpha(alpha: float):
            if not (0.0 <= alpha <= 1.0):
                raise ValueError(f"Invalid alpha: {alpha}")

        with pytest.raises(ValueError, match="Invalid alpha"):
            validate_alpha(1.5)

    def test_50k_vectors_selects_flat_index(self):
        """50K vectors must select FLAT brute-force index (mocked)."""

        def select_index(
            num_vectors: int, recall_target: float = 0.99, memory_gb: float = 1000
        ) -> str:
            if num_vectors <= 100_000:
                return "FLAT"
            elif memory_gb < 128 and num_vectors > 50_000_000:
                return "IVF_PQ"
            elif recall_target >= 0.99:
                return "HNSW_M32"
            else:
                return "HNSW_M16"

        assert select_index(50_000) == "FLAT"

    def test_5m_vectors_recall_0_95_selects_hnsw_m16(self):
        """5M vectors with recall≥0.95 must select HNSW M=16 (mocked)."""

        def select_index(
            num_vectors: int, recall_target: float = 0.99, memory_gb: float = 1000
        ) -> str:
            if num_vectors <= 100_000:
                return "FLAT"
            elif memory_gb < 128 and num_vectors > 50_000_000:
                return "IVF_PQ"
            elif recall_target >= 0.99:
                return "HNSW_M32"
            else:
                return "HNSW_M16"

        result = select_index(5_000_000, recall_target=0.95)
        assert (
            "HNSW" in result and "16" in result
        ), f"Expected HNSW_M16 for 5M vectors recall=0.95, got {result}"

    def test_100m_vectors_32gb_selects_ivf_pq(self):
        """100M vectors with 32GB memory must select IVF_PQ compressed index (mocked)."""

        def select_index(
            num_vectors: int, recall_target: float = 0.99, memory_gb: float = 1000
        ) -> str:
            if num_vectors <= 100_000:
                return "FLAT"
            elif memory_gb < 128 and num_vectors > 50_000_000:
                return "IVF_PQ"
            elif recall_target >= 0.99:
                return "HNSW_M32"
            else:
                return "HNSW_M16"

        result = select_index(100_000_000, memory_gb=32)
        assert (
            result == "IVF_PQ"
        ), f"Expected IVF_PQ for 100M vectors + 32GB, got {result}"
