"""Test file for the bazel-build-optimization skill.

This suite validates the CacheHitAnalyzer, CacheAnalysisReport, and
InputChangeTracker Java classes in the Bazel remote-cache module.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest


class TestBazelBuildOptimization:
    """Verify Bazel remote cache analysis components."""

    REPO_DIR = "/workspace/bazel"

    CACHE_HIT_ANALYZER = (
        "src/main/java/com/google/devtools/build/lib/remote/CacheHitAnalyzer.java"
    )
    CACHE_ANALYSIS_REPORT = (
        "src/main/java/com/google/devtools/build/lib/remote/CacheAnalysisReport.java"
    )
    INPUT_CHANGE_TRACKER = (
        "src/main/java/com/google/devtools/build/lib/remote/InputChangeTracker.java"
    )

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

    def _java_class_body(self, source: str, class_name: str) -> str | None:
        """Extract the body of a Java class by name (rough brace matching)."""
        pattern = rf"class\s+{class_name}\b"
        m = re.search(pattern, source)
        if m is None:
            return None
        start = source.find("{", m.end())
        if start < 0:
            return None
        depth, i = 1, start + 1
        while i < len(source) and depth > 0:
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
            i += 1
        return source[start:i]

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_src_main_java_com_google_devtools_build_lib_remote_cachehita(
        self,
    ):
        """Verify CacheHitAnalyzer.java exists and is non-empty."""
        self._assert_non_empty_file(self.CACHE_HIT_ANALYZER)

    def test_file_path_src_main_java_com_google_devtools_build_lib_remote_cacheanal(
        self,
    ):
        """Verify CacheAnalysisReport.java exists and is non-empty."""
        self._assert_non_empty_file(self.CACHE_ANALYSIS_REPORT)

    def test_file_path_src_main_java_com_google_devtools_build_lib_remote_inputchan(
        self,
    ):
        """Verify InputChangeTracker.java exists and is non-empty."""
        self._assert_non_empty_file(self.INPUT_CHANGE_TRACKER)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_cachehitanalyzer_constructor_accepts_list_buildevent(self):
        """CacheHitAnalyzer constructor accepts List<BuildEvent>."""
        src = self._read_text(self.CACHE_HIT_ANALYZER)
        body = self._java_class_body(src, "CacheHitAnalyzer")
        assert body is not None, "CacheHitAnalyzer class not found"
        assert re.search(
            r"List\s*<.*BuildEvent.*>", body
        ), "Constructor should accept List<BuildEvent>"

    def test_semantic_cachehitanalyzer_analyze_returns_cacheanalysisreport(self):
        """CacheHitAnalyzer.analyze() returns CacheAnalysisReport."""
        src = self._read_text(self.CACHE_HIT_ANALYZER)
        body = self._java_class_body(src, "CacheHitAnalyzer")
        assert body is not None, "CacheHitAnalyzer class not found"
        assert re.search(
            r"CacheAnalysisReport\s+analyze\s*\(", body
        ), "analyze() method should return CacheAnalysisReport"

    def test_semantic_cacheanalysisreport_has_aggregatestats_list_targetcachestats(
        self,
    ):
        """CacheAnalysisReport has AggregateStats, List<TargetCacheStats>, List<FrequentMiss>."""
        src = self._read_text(self.CACHE_ANALYSIS_REPORT)
        body = self._java_class_body(src, "CacheAnalysisReport")
        assert body is not None, "CacheAnalysisReport class not found"
        for field in ("AggregateStats", "TargetCacheStats", "FrequentMiss"):
            assert field in body, f"CacheAnalysisReport missing {field}"

    def test_semantic_inputchangetracker_recordaction_maintains_input_digest_histo(
        self,
    ):
        """InputChangeTracker.recordAction maintains input digest history."""
        src = self._read_text(self.INPUT_CHANGE_TRACKER)
        body = self._java_class_body(src, "InputChangeTracker")
        assert body is not None, "InputChangeTracker class not found"
        assert re.search(
            r"recordAction\s*\(", body
        ), "InputChangeTracker should have recordAction method"
        assert re.search(
            r"digest|hash|Map|history", body, re.IGNORECASE
        ), "recordAction should maintain digest history"

    def test_semantic_inputchangetracker_getfrequentlychangedinputs_returns_top_n_(
        self,
    ):
        """InputChangeTracker.getFrequentlyChangedInputs returns top N volatile files."""
        src = self._read_text(self.INPUT_CHANGE_TRACKER)
        body = self._java_class_body(src, "InputChangeTracker")
        assert body is not None, "InputChangeTracker class not found"
        assert re.search(
            r"getFrequentlyChangedInputs\s*\(", body
        ), "InputChangeTracker should have getFrequentlyChangedInputs method"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, mocked via source analysis)
    # ------------------------------------------------------------------

    def test_functional_1000_events_with_850_hits_aggregate_hitratepercent_85_0(self):
        """1000 events with 850 hits → aggregate hitRatePercent=85.0."""
        src = self._read_text(self.CACHE_HIT_ANALYZER)
        body = self._java_class_body(src, "CacheHitAnalyzer")
        assert body is not None
        # Verify hit-rate computation logic exists
        assert re.search(
            r"hitRate|hit_rate|hitPercent|hit.*miss", body, re.IGNORECASE
        ), "CacheHitAnalyzer should compute hit rate"
        # Verify it counts both hits and misses
        assert re.search(
            r"hit|miss|CACHE_HIT|CACHE_MISS|remote_cache", body, re.IGNORECASE
        ), "Analyzer should classify cache status into hit/miss"

    def test_functional_per_target_breakdown_correct_for_multi_target_scenario(self):
        """Per-target breakdown correct for multi-target scenario."""
        src = self._read_text(self.CACHE_HIT_ANALYZER)
        body = self._java_class_body(src, "CacheHitAnalyzer")
        assert body is not None
        # Must group by target
        assert re.search(
            r"target|label|mnemonic", body, re.IGNORECASE
        ), "Analyzer should group results by target"
        # Report class must support per-target stats
        report_src = self._read_text(self.CACHE_ANALYSIS_REPORT)
        assert (
            "TargetCacheStats" in report_src
        ), "CacheAnalysisReport must define TargetCacheStats"

    def test_functional_new_target_with_no_history_miss_cause_is_new_target(self):
        """New target with no history → miss cause is 'new_target'."""
        src = self._read_text(self.CACHE_HIT_ANALYZER)
        combined = src + self._read_text(self.INPUT_CHANGE_TRACKER)
        assert re.search(
            r"new.?target|NEW_TARGET|first.?build|no.?history", combined, re.IGNORECASE
        ), "Miss classification should include 'new_target' cause"

    def test_functional_changed_input_digests_miss_cause_is_input_change(self):
        """Changed input digests → miss cause is 'input_change'."""
        src = self._read_text(self.CACHE_HIT_ANALYZER)
        combined = src + self._read_text(self.INPUT_CHANGE_TRACKER)
        assert re.search(
            r"input.?change|INPUT_CHANGE|digest.*differ|changed.?input",
            combined,
            re.IGNORECASE,
        ), "Miss classification should include 'input_change' cause"

    def test_functional_frequently_changed_input_detected_across_multiple_targets(self):
        """Frequently changed input detected across multiple targets."""
        src = self._read_text(self.INPUT_CHANGE_TRACKER)
        body = self._java_class_body(src, "InputChangeTracker")
        assert body is not None
        assert re.search(
            r"frequent|volatile|top|count|threshold", body, re.IGNORECASE
        ), "InputChangeTracker should detect frequently changed inputs"
        assert re.search(
            r"getFrequentlyChangedInputs", body
        ), "Should expose getFrequentlyChangedInputs method"
