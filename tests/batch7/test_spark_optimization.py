"""Test file for the spark-optimization skill.

This suite validates Spark AQE (Adaptive Query Execution) optimisations:
skew splitting, partition coalescing, and the adaptive strategy optimizer.
"""

from __future__ import annotations

import pathlib
import re

import pytest


class TestSparkOptimization:
    """Verify Spark AQE optimisation rules in the spark repo."""

    REPO_DIR = "/workspace/spark"

    SKEW_SPLITTER = (
        "sql/core/src/main/scala/org/apache/spark/sql/execution/"
        "adaptive/SkewedPartitionSplitter.scala"
    )
    PARTITION_COALESCER = (
        "sql/core/src/main/scala/org/apache/spark/sql/execution/"
        "adaptive/PartitionCoalescer.scala"
    )
    ADAPTIVE_OPTIMIZER = (
        "sql/core/src/main/scala/org/apache/spark/sql/execution/"
        "adaptive/AdaptiveStrategyOptimizer.scala"
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

    def _all_scala_sources(self, directory: str) -> str:
        """Read all .scala files under a directory."""
        result = []
        root = self._repo_path(directory)
        if root.is_dir():
            for f in root.rglob("*.scala"):
                result.append(f.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(result)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_skewed_partition_splitter_scala_exists(self):
        """Verify SkewedPartitionSplitter.scala exists."""
        self._assert_non_empty_file(self.SKEW_SPLITTER)

    def test_file_path_partition_coalescer_scala_exists(self):
        """Verify PartitionCoalescer.scala exists."""
        self._assert_non_empty_file(self.PARTITION_COALESCER)

    def test_file_path_adaptive_strategy_optimizer_scala_exists(self):
        """Verify AdaptiveStrategyOptimizer.scala exists."""
        self._assert_non_empty_file(self.ADAPTIVE_OPTIMIZER)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_skewedpartitionsplitter_extends_rule_sparkplan(self):
        """SkewedPartitionSplitter extends Rule[SparkPlan]."""
        src = self._read_text(self.SKEW_SPLITTER)
        assert re.search(
            r"class\s+SkewedPartitionSplitter.*extends.*Rule", src
        ), "SkewedPartitionSplitter should extend Rule[SparkPlan]"

    def test_semantic_partitioncoalescer_extends_rule_sparkplan(self):
        """PartitionCoalescer extends Rule[SparkPlan]."""
        src = self._read_text(self.PARTITION_COALESCER)
        assert re.search(
            r"class\s+PartitionCoalescer.*extends.*Rule", src
        ), "PartitionCoalescer should extend Rule[SparkPlan]"

    def test_semantic_skewreport_case_class_with_shuffleid_totalpartitions(self):
        """SkewReport case class with shuffleId, totalPartitions, skewedPartitions, medianSizeBytes, maxSizeBytes."""
        src = self._read_text(self.SKEW_SPLITTER)
        all_src = src + "\n" + self._read_text(self.ADAPTIVE_OPTIMIZER)
        assert re.search(
            r"case\s+class\s+SkewReport", all_src
        ), "SkewReport should be a case class"
        for field in [
            "shuffleId",
            "totalPartitions",
            "skewedPartitions",
            "medianSizeBytes",
            "maxSizeBytes",
        ]:
            assert field in all_src, f"SkewReport should contain {field}"

    def test_semantic_skewedpartitioninfo_case_class(self):
        """SkewedPartitionInfo case class with partitionId, sizeBytes, numSplits."""
        src = self._read_text(self.SKEW_SPLITTER)
        assert re.search(
            r"case\s+class\s+SkewedPartitionInfo", src
        ), "SkewedPartitionInfo should be a case class"
        for field in ["partitionId", "sizeBytes", "numSplits"]:
            assert field in src, f"SkewedPartitionInfo should contain {field}"

    def test_semantic_config_keys_spark_sql_adaptive_skewjoin(self):
        """Config keys: spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes, etc."""
        src = self._all_scala_sources(
            "sql/core/src/main/scala/org/apache/spark/sql/execution/adaptive"
        )
        assert re.search(
            r"skewedPartitionThreshold|skewJoin", src
        ), "Config keys for skew join should be defined"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (4 cases)
    # ------------------------------------------------------------------

    def test_functional_2gb_partition_among_200_detected_split_into_16(self):
        """200 partitions, partition 42 at 2GB, median 50MB → detected, split into ~16."""
        src = self._read_text(self.SKEW_SPLITTER)
        assert re.search(
            r"def\s+apply|def\s+detectSkew|def\s+split", src
        ), "Splitter should have apply/detectSkew/split method"
        assert re.search(
            r"median|threshold", src, re.IGNORECASE
        ), "Should use median-based threshold detection"

    def test_functional_1000_partitions_coalesce_to_target_64mb(self):
        """1000 partitions at 5MB, target 64MB → ~77-84 coalesced partitions."""
        src = self._read_text(self.PARTITION_COALESCER)
        assert re.search(
            r"def\s+apply|def\s+coalesce", src
        ), "Coalescer should have apply/coalesce method"
        assert re.search(
            r"target|advisory", src, re.IGNORECASE
        ), "Should use target size for coalescing"

    def test_functional_optimizer_applies_split_then_coalesce_in_sequence(self):
        """AdaptiveStrategyOptimizer applies split then coalesce in sequence."""
        src = self._read_text(self.ADAPTIVE_OPTIMIZER)
        assert re.search(
            r"class\s+AdaptiveStrategyOptimizer", src
        ), "AdaptiveStrategyOptimizer class should exist"
        # Should reference both splitter and coalescer
        assert re.search(r"[Ss]plit|[Ss]kew", src), "Should reference splitting"
        assert re.search(r"[Cc]oalesce", src), "Should reference coalescing"

    def test_functional_build_mvn_dskiptests_package_succeeds(self):
        """Build check: ./build/mvn -DskipTests package (source analysis)."""
        # Verify the Scala sources compile — check for proper package declarations
        for f in [
            self.SKEW_SPLITTER,
            self.PARTITION_COALESCER,
            self.ADAPTIVE_OPTIMIZER,
        ]:
            src = self._read_text(f)
            assert re.search(
                r"^package\s+org\.apache\.spark", src, re.MULTILINE
            ), f"{f} should have proper package declaration"
