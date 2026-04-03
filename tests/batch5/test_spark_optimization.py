"""
Test for 'spark-optimization' skill — Spark/Scala Fiscal Job Optimization
Validates Scala FiscalJob, UDF month→quarter mapping, AQE (Adaptive Query
Execution), broadcast join, and Spark SQL optimizations.
"""

import os
import re

import pytest


class TestSparkOptimization:
    """Verify Spark optimization patterns."""

    REPO_DIR = "/workspace/spark"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_spark_source_exists(self):
        """Verify Spark source directory exists."""
        assert os.path.isdir(self.REPO_DIR), "Spark repo not found"

    def test_scala_files_exist(self):
        """Verify Scala source files exist."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".scala"):
                    found = True
                    break
            if found:
                break
        assert found, "No Scala files found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_fiscal_job(self):
        """Verify FiscalJob or fiscal quarter processing."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(FiscalJob|fiscal|quarter|FiscalQuarter)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No FiscalJob/fiscal processing found")

    def test_udf_month_to_quarter(self):
        """Verify UDF for month to fiscal quarter mapping."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(r"(udf|UDF|UserDefinedFunction)", content) and re.search(
                r"(month|quarter)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No UDF month-to-quarter mapping found")

    def test_aqe_enabled(self):
        """Verify Adaptive Query Execution (AQE) configuration."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(adaptive|AQE|spark\.sql\.adaptive|adaptiveExecutionEnabled)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No AQE configuration found")

    def test_broadcast_join(self):
        """Verify broadcast join optimization."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(broadcast|BroadcastHashJoin|broadcast_join|autoBroadcastJoinThreshold)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No broadcast join optimization found")

    def test_partition_optimization(self):
        """Verify partition/repartition optimization."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(repartition|coalesce|shuffle\.partitions|numPartitions)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No partition optimization found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_build_file_exists(self):
        """Verify build configuration (build.sbt, pom.xml, etc.)."""
        build_files = ["build.sbt", "pom.xml", "build.gradle"]
        for bf in build_files:
            if os.path.exists(os.path.join(self.REPO_DIR, bf)):
                return
        pytest.fail("No build file (build.sbt/pom.xml) found")

    def test_spark_sql_usage(self):
        """Verify Spark SQL usage."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(r"(spark\.sql|SparkSession|DataFrame|Dataset|sql\()", content):
                return
        pytest.fail("No Spark SQL usage found")

    def test_caching_strategy(self):
        """Verify caching/persistence strategy."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(\.cache\(\)|\.persist\(\)|MEMORY_AND_DISK|StorageLevel)", content
            ):
                return
        pytest.fail("No caching strategy found")

    def test_spark_config(self):
        """Verify SparkConf / SparkSession configuration."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(SparkConf|SparkSession\.builder|\.config\(|spark\.conf)", content
            ):
                return
        pytest.fail("No SparkConf/SparkSession config found")

    def test_serialization_optimization(self):
        """Verify serialization optimization (Kryo, etc.)."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(Kryo|KryoSerializer|spark\.serializer|registerKryoClasses)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.skip("No Kryo serialization found (may use default)")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_source_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith((".scala", ".java", ".py", ".xml", ".conf")):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
