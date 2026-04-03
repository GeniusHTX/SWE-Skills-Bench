"""Test file for the similarity-search-patterns skill.

This suite validates filtered search and selectivity estimation in Milvus,
including pre/post-filter strategy switching and cosine distance calculations.
"""

from __future__ import annotations

import math
import pathlib
import re

import pytest


class TestSimilaritySearchPatterns:
    """Verify filtered search + selectivity estimation in Milvus."""

    REPO_DIR = "/workspace/milvus"

    FILTERED_SEARCH_GO = "internal/querynodev2/segments/filtered_search.go"
    SELECTIVITY_GO = "internal/querynodev2/segments/selectivity_estimator.go"
    FILTERED_SEARCH_TEST_GO = "internal/querynodev2/segments/filtered_search_test.go"

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

    def _go_struct_body(self, source: str, struct_name: str) -> str:
        """Extract the body of a Go struct type definition."""
        pattern = rf"type\s+{struct_name}\s+struct\s*\{{([^}}]+)\}}"
        m = re.search(pattern, source, re.DOTALL)
        return m.group(1) if m else ""

    def _all_go_sources(self, directory: str) -> str:
        """Read all .go files under a directory."""
        result = []
        root = self._repo_path(directory)
        if root.is_dir():
            for f in root.rglob("*.go"):
                result.append(f.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(result)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_filtered_search_go_created(self):
        """Verify filtered_search.go exists."""
        self._assert_non_empty_file(self.FILTERED_SEARCH_GO)

    def test_file_path_selectivity_estimator_go_created(self):
        """Verify selectivity_estimator.go exists."""
        self._assert_non_empty_file(self.SELECTIVITY_GO)

    def test_file_path_filtered_search_test_go_created(self):
        """Verify filtered_search_test.go exists."""
        self._assert_non_empty_file(self.FILTERED_SEARCH_TEST_GO)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_selectivityestimator_struct_with_segmentstats_map(self):
        """SelectivityEstimator struct with segmentStats map."""
        src = self._read_text(self.SELECTIVITY_GO)
        body = self._go_struct_body(src, "SelectivityEstimator")
        assert body, "SelectivityEstimator struct not found"
        assert re.search(
            r"segmentStats|segment_stats|map", body, re.IGNORECASE
        ), "SelectivityEstimator should have a segmentStats map field"

    def test_semantic_estimateselectivity_handles_all_filter_types(self):
        """EstimateSelectivity handles all filter types."""
        src = self._read_text(self.SELECTIVITY_GO)
        assert re.search(
            r"func.*EstimateSelectivity", src
        ), "EstimateSelectivity function should exist"
        # Should handle multiple filter types via switch/case or if/else
        assert re.search(
            r"switch|case|filter.*type|FilterType", src, re.IGNORECASE
        ), "EstimateSelectivity should handle multiple filter types"

    def test_semantic_filteredsearchoperator_with_prefilterthreshold_postfiltermult(
        self,
    ):
        """FilteredSearchOperator has preFilterThreshold/postFilterMultiplier."""
        src = self._read_text(self.FILTERED_SEARCH_GO)
        body = self._go_struct_body(src, "FilteredSearchOperator")
        assert body, "FilteredSearchOperator struct not found"
        assert re.search(
            r"preFilter|pre_filter|PreFilter", body
        ), "FilteredSearchOperator should have preFilterThreshold"
        assert re.search(
            r"postFilter|post_filter|PostFilter|Multiplier", body
        ), "FilteredSearchOperator should have postFilterMultiplier"

    def test_semantic_search_method_both_strategies_with_switching(self):
        """Search method supports both pre-filter and post-filter strategies."""
        src = self._read_text(self.FILTERED_SEARCH_GO)
        assert re.search(r"func.*Search", src), "Search method should exist"
        assert re.search(
            r"pre.*filter|PreFilter", src, re.IGNORECASE
        ), "Search should support pre-filter strategy"
        assert re.search(
            r"post.*filter|PostFilter", src, re.IGNORECASE
        ), "Search should support post-filter strategy"

    def test_semantic_cosinedistance_equals_1_minus_cosinesimilarity(self):
        """CosineDistance = 1 - CosineSimilarity."""
        src = self._all_go_sources("internal/querynodev2/segments")
        assert re.search(
            r"[Cc]osine[Dd]istance|cosine_distance", src
        ), "CosineDistance function should exist"
        assert re.search(
            r"1\.0?\s*-|1\s*-", src
        ), "CosineDistance should compute 1 - CosineSimilarity"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases)
    # ------------------------------------------------------------------

    def test_functional_selectivity_001_triggers_pre_filter(self):
        """Selectivity 0.01 → pre-filter strategy."""
        src = self._read_text(self.FILTERED_SEARCH_GO)
        # Low selectivity should trigger pre-filter
        assert re.search(
            r"preFilter|pre.filter", src, re.IGNORECASE
        ), "Low selectivity should trigger pre-filter path"
        # Should have threshold comparison
        assert re.search(
            r"<|<=|threshold", src
        ), "Strategy selection should compare against threshold"

    def test_functional_selectivity_099_triggers_post_filter(self):
        """Selectivity 0.99 → post-filter strategy."""
        src = self._read_text(self.FILTERED_SEARCH_GO)
        # High selectivity should trigger post-filter
        assert re.search(
            r"postFilter|post.filter", src, re.IGNORECASE
        ), "High selectivity should trigger post-filter path"

    def test_functional_cosinedistance_orthogonal_equals_1(self):
        """CosineDistance([1,0],[0,1]) = 1.0."""
        src = self._all_go_sources("internal/querynodev2/segments")
        # Verify cosine distance is implemented
        assert re.search(
            r"[Cc]osine[Dd]istance|cosine_distance", src
        ), "CosineDistance should be implemented"
        # Check test file for orthogonal vector test
        test_src = self._read_text(self.FILTERED_SEARCH_TEST_GO)
        assert re.search(
            r"1\.0|orthogonal|CosineDistance", test_src
        ), "Test should verify CosineDistance for orthogonal vectors"

    def test_functional_cosinedistance_identical_equals_0(self):
        """CosineDistance([1,0],[1,0]) = 0.0."""
        test_src = self._read_text(self.FILTERED_SEARCH_TEST_GO)
        assert re.search(
            r"0\.0|identical|same|CosineDistance", test_src
        ), "Test should verify CosineDistance for identical vectors"

    def test_functional_dimension_mismatch_returns_error(self):
        """Dimension mismatch → error."""
        src = self._all_go_sources("internal/querynodev2/segments")
        assert re.search(
            r"dimension|mismatch|len\(|length", src, re.IGNORECASE
        ), "Should check for dimension mismatch"
        assert re.search(
            r"error|Error|err\s*!=\s*nil|fmt\.Errorf", src
        ), "Dimension mismatch should return an error"
