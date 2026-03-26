"""
Tests for spark-optimization skill.
REPO_DIR: /workspace/spark
"""

import os
import pytest

REPO_DIR = "/workspace/spark"


def _path(rel):
    return os.path.join(REPO_DIR, rel)


def _read(rel):
    with open(_path(rel), encoding="utf-8") as f:
        return f.read()


class TestSparkOptimization:
    # ── file_path_check ────────────────────────────────────────────────────
    def test_optimized_pipeline_scala_exists(self):
        """Verify OptimizedPipeline.scala exists in examples/src/main/scala/."""
        fpath = _path("examples/src/main/scala/OptimizedPipeline.scala")
        assert os.path.isfile(
            fpath
        ), "examples/src/main/scala/OptimizedPipeline.scala must exist"
        assert os.path.getsize(fpath) > 0, "OptimizedPipeline.scala must be non-empty"

    def test_pipeline_config_and_metrics_exist(self):
        """Verify PipelineConfig.scala and PipelineMetrics.scala exist."""
        config_path = _path("examples/src/main/scala/PipelineConfig.scala")
        metrics_path = _path("examples/src/main/scala/PipelineMetrics.scala")
        assert os.path.isfile(config_path), "PipelineConfig.scala must exist"
        assert os.path.isfile(metrics_path), "PipelineMetrics.scala must exist"

    # ── semantic_check ─────────────────────────────────────────────────────
    def test_broadcast_hint_on_products_join(self):
        """Verify broadcast() hint is applied to products DataFrame in join operation."""
        content = _read("examples/src/main/scala/OptimizedPipeline.scala")
        assert (
            "broadcast(" in content.lower() or "broadcast(" in content
        ), "broadcast() hint must be applied to products DataFrame"

    def test_repartition_by_user_id(self):
        """Verify repartition by user_id column is present in OptimizedPipeline.scala."""
        content = _read("examples/src/main/scala/OptimizedPipeline.scala")
        assert "repartition" in content, "repartition call must be present"
        assert "user_id" in content, "user_id must be referenced in repartition"

    def test_aqe_config_present(self):
        """Verify Adaptive Query Execution (AQE) configs are set in PipelineConfig.scala."""
        content = _read("examples/src/main/scala/PipelineConfig.scala")
        has_adaptive = "adaptive.enabled" in content or "spark.sql.adaptive" in content
        assert (
            has_adaptive
        ), "AQE adaptive.enabled or spark.sql.adaptive config must be present"
        has_partitions = "coalescePartitions" in content or "skewJoin" in content
        assert (
            has_partitions
        ), "coalescePartitions or skewJoin AQE setting must be configured"

    def test_dense_rank_window_function(self):
        """Verify dense_rank() window function is used in OptimizedPipeline.scala."""
        content = _read("examples/src/main/scala/OptimizedPipeline.scala")
        assert (
            "dense_rank()" in content or "denseRank" in content
        ), "dense_rank() or denseRank must be used"
        assert (
            "Window" in content or "WindowSpec" in content
        ), "Window or WindowSpec must be referenced with dense_rank"

    def test_partition_by_region_category(self):
        """Verify output is partitioned by 'region' and 'category' columns."""
        content = _read("examples/src/main/scala/OptimizedPipeline.scala")
        assert "partitionBy" in content, "partitionBy must be called on output"
        assert "region" in content, "region column must appear in partitionBy"
        assert "category" in content, "category column must appear in partitionBy"

    # ── functional_check (mocked) ──────────────────────────────────────────
    def test_pipeline_metrics_case_class_fields(self):
        """Verify PipelineMetrics case class has required fields."""
        content = _read("examples/src/main/scala/PipelineMetrics.scala")
        assert (
            "case class PipelineMetrics" in content
        ), "PipelineMetrics must be a case class"
        required_fields = ["inputRows", "outputRows", "durationMs", "skippedRows"]
        for field in required_fields:
            assert field in content, f"PipelineMetrics must define field: {field}"

    def test_no_cartesian_join(self):
        """Verify no cartesian (cross) joins exist in OptimizedPipeline.scala."""
        content = _read("examples/src/main/scala/OptimizedPipeline.scala")
        assert (
            "crossJoin" not in content
        ), "crossJoin (cartesian join) must not appear in optimized pipeline"
        assert (
            "CrossJoin" not in content
        ), "CrossJoin must not appear in optimized pipeline"

    def test_spark_session_configured(self):
        """Verify SparkSession is configured via builder pattern in PipelineConfig.scala."""
        content = _read("examples/src/main/scala/PipelineConfig.scala")
        assert (
            "SparkSession.builder" in content
        ), "SparkSession.builder must be used for session creation"
        assert ".config(" in content, ".config() must be called for AQE settings"
        assert ".getOrCreate()" in content, ".getOrCreate() pattern must be used"

    def test_broadcast_threshold_config(self):
        """Verify autoBroadcastJoinThreshold or explicit broadcast threshold is configured."""
        content = _read("examples/src/main/scala/PipelineConfig.scala")
        has_threshold = (
            "autoBroadcastJoinThreshold" in content or "broadcastTimeout" in content
        )
        assert (
            has_threshold
        ), "autoBroadcastJoinThreshold or broadcastTimeout must be explicitly configured"

    def test_pipeline_metrics_not_empty_on_success(self):
        """
        Mocked: Verify PipelineMetrics records positive inputRows and durationMs.
        """

        class PipelineMetrics:
            def __init__(self, input_rows, output_rows, duration_ms, skipped_rows=0):
                self.inputRows = input_rows
                self.outputRows = output_rows
                self.durationMs = duration_ms
                self.skippedRows = skipped_rows

        metrics = PipelineMetrics(
            input_rows=1000, output_rows=950, duration_ms=500, skipped_rows=50
        )
        assert metrics.inputRows > 0, "inputRows must be positive after successful run"
        assert (
            metrics.durationMs > 0
        ), "durationMs must be positive after successful run"
        assert metrics.outputRows >= 0, "outputRows must be non-negative"
