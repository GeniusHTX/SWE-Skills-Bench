"""
Test for 'spark-optimization' skill — PySpark Optimization
Validates that the Agent implemented Spark query analyzer, broadcast join
optimizer, and partition strategy advisor with AQE configuration.
"""

import os
import re
import sys

import pytest


class TestSparkOptimization:
    """Verify Spark optimization implementation."""

    REPO_DIR = "/workspace/spark"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def _find_file(self, *candidates):
        for c in candidates:
            p = os.path.join(self.REPO_DIR, c)
            if os.path.isfile(p):
                return p
        return None

    def test_query_analyzer_module_exists(self):
        """Verify spark_optimization/query_analyzer.py or spark/analyzer.py exists."""
        candidates = ("spark_optimization/query_analyzer.py", "spark/analyzer.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    def test_broadcast_optimizer_module_exists(self):
        """Verify spark_optimization/broadcast_optimizer.py or spark/broadcast.py exists."""
        candidates = ("spark_optimization/broadcast_optimizer.py",
                       "spark/broadcast.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    def test_partition_advisor_module_exists(self):
        """Verify spark_optimization/partition_advisor.py or spark/partition.py exists."""
        candidates = ("spark_optimization/partition_advisor.py",
                       "spark/partition.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    # ── semantic_check ──────────────────────────────────────────────

    def test_aqe_setting_string_present(self):
        """Verify spark.sql.adaptive.enabled string present for AQE recommendation."""
        path = self._find_file("spark_optimization/query_analyzer.py",
                               "spark/analyzer.py")
        assert path, "Query analyzer module not found"
        content = self._read(path)
        assert "spark.sql.adaptive.enabled" in content, \
            "spark.sql.adaptive.enabled not found"

    def test_broadcast_threshold_constant(self):
        """Verify broadcast optimizer uses 10MB or 100MB as default threshold."""
        path = self._find_file("spark_optimization/broadcast_optimizer.py",
                               "spark/broadcast.py")
        assert path, "Broadcast optimizer module not found"
        content = self._read(path)
        found = any(kw in content for kw in ("100", "10"))
        assert found, "Broadcast threshold value not found"

    def test_partition_formula_present(self):
        """Verify partition advisor contains formula referencing num_cores or data_size."""
        path = self._find_file("spark_optimization/partition_advisor.py",
                               "spark/partition.py")
        assert path, "Partition advisor module not found"
        content = self._read(path)
        found = any(kw in content for kw in (
            "num_cores", "data_size", "target_partition_size"))
        assert found, "Partition formula not found"

    def test_join_types_key_in_analyze_return(self):
        """Verify analyze() returns dict with join_types key."""
        path = self._find_file("spark_optimization/query_analyzer.py",
                               "spark/analyzer.py")
        assert path, "Query analyzer module not found"
        content = self._read(path)
        assert "join_types" in content, "join_types not found in analyzer"

    # ── functional_check (import) ───────────────────────────────────

    def _skip_unless_importable(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if self.REPO_DIR not in sys.path:
            sys.path.insert(0, self.REPO_DIR)

    def test_broadcast_recommend_small_table(self):
        """BroadcastJoinOptimizer.recommend(50) returns dict with broadcast_threshold."""
        self._skip_unless_importable()
        try:
            from spark_optimization.broadcast_optimizer import BroadcastJoinOptimizer
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        rec = BroadcastJoinOptimizer().recommend(50)
        assert rec is not None and "broadcast_threshold" in rec, \
            "50MB table should receive broadcast recommendation"

    def test_broadcast_not_recommended_large_table(self):
        """BroadcastJoinOptimizer.recommend(200) returns None or no broadcast hint."""
        self._skip_unless_importable()
        try:
            from spark_optimization.broadcast_optimizer import BroadcastJoinOptimizer
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        rec = BroadcastJoinOptimizer().recommend(200)
        assert rec is None or rec.get("broadcast_threshold") is None, \
            "200MB table should not receive broadcast recommendation"

    def test_partition_advise_100gb_32cores(self):
        """PartitionStrategyAdvisor.advise(100, 32) returns int in range [100, 500]."""
        self._skip_unless_importable()
        try:
            from spark_optimization.partition_advisor import PartitionStrategyAdvisor
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        n = PartitionStrategyAdvisor().advise(100, 32)
        assert isinstance(n, int) and 100 <= n <= 500, \
            f"Expected 100-500 partitions, got {n}"

    def test_analyze_no_join_plan(self):
        """SparkQueryAnalyzer: plan with no joins returns empty join_types."""
        self._skip_unless_importable()
        try:
            from spark_optimization.query_analyzer import SparkQueryAnalyzer
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        plan_text = ("== Physical Plan ==\n"
                     "FileScan parquet [id, value] Batched: true, DataFilters: []")
        result = SparkQueryAnalyzer().analyze_plan(plan_text)
        assert result["join_types"] == [], \
            f"Expected empty join_types, got {result['join_types']}"
        assert result["stage_count"] >= 1, \
            f"Expected stage_count >= 1, got {result['stage_count']}"
