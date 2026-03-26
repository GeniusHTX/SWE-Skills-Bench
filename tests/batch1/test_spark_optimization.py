"""
Test for 'spark-optimization' skill — Apache Spark Query Optimization
Validates that the Agent created optimized Spark query examples with
proper partitioning, caching, and broadcast join patterns.
"""

import os
import subprocess
import pytest


class TestSparkOptimization:
    """Verify Spark optimization demo scripts."""

    REPO_DIR = "/workspace/spark"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_demo_script_exists(self):
        """An optimization demo script must exist."""
        examples_dir = os.path.join(self.REPO_DIR, "examples", "src", "main")
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if "optim" in f.lower() and (
                    f.endswith(".py") or f.endswith(".scala") or f.endswith(".java")
                ):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No optimization demo file found"

    def test_readme_exists(self):
        """README or doc for optimization examples must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.lower() == "readme.md" and "optim" in root.lower():
                    found = True
                    break
            if found:
                break
        if not found:
            # Also check for inline docs in the script
            for root, dirs, files in os.walk(self.REPO_DIR):
                for f in files:
                    if "optim" in f.lower() and f.endswith((".py", ".scala")):
                        fpath = os.path.join(root, f)
                        with open(fpath, "r", errors="ignore") as fh:
                            content = fh.read()
                        if len(content) > 200:
                            found = True
                            break
                if found:
                    break
        assert found, "No README or substantial docs for optimization examples"

    # ------------------------------------------------------------------
    # L2: content validation
    # ------------------------------------------------------------------

    def _find_demo_files(self):
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if "optim" in f.lower() and (
                    f.endswith(".py") or f.endswith(".scala") or f.endswith(".java")
                ):
                    found.append(os.path.join(root, f))
        return found

    def _read_all_demos(self):
        content = ""
        for fpath in self._find_demo_files():
            with open(fpath, "r", errors="ignore") as f:
                content += f.read() + "\n"
        return content

    def test_broadcast_join(self):
        """Demo must show broadcast join optimization."""
        content = self._read_all_demos()
        patterns = [
            "broadcast",
            "BroadcastHashJoin",
            "broadcast_join",
            "F.broadcast",
            "spark.sql.autoBroadcastJoinThreshold",
        ]
        found = any(p in content for p in patterns)
        assert found, "No broadcast join pattern found"

    def test_caching_strategy(self):
        """Demo must show caching (persist/cache)."""
        content = self._read_all_demos()
        patterns = [
            ".cache()",
            ".persist()",
            "MEMORY_AND_DISK",
            "StorageLevel",
            "unpersist",
        ]
        found = any(p in content for p in patterns)
        assert found, "No caching strategy found"

    def test_partitioning(self):
        """Demo must show repartition or coalesce."""
        content = self._read_all_demos()
        patterns = [
            "repartition",
            "coalesce",
            "partitionBy",
            "numPartitions",
            "spark.sql.shuffle.partitions",
        ]
        found = any(p in content for p in patterns)
        assert found, "No partitioning strategy found"

    def test_predicate_pushdown(self):
        """Demo should demonstrate predicate pushdown or filter early."""
        content = self._read_all_demos()
        patterns = ["filter", "where", "pushdown", "predicate", ".filter(", ".where("]
        found = any(p in content for p in patterns)
        assert found, "No predicate pushdown/filter pattern found"

    def test_explain_plan(self):
        """Demo should use .explain() to show query plans."""
        content = self._read_all_demos()
        patterns = [
            ".explain(",
            "EXPLAIN",
            "queryExecution",
            "logical plan",
            "physical plan",
        ]
        found = any(p in content for p in patterns)
        assert found, "No explain plan usage found"

    def test_avoid_shuffle(self):
        """Demo should discuss or address shuffle reduction."""
        content = self._read_all_demos()
        patterns = [
            "shuffle",
            "reduceByKey",
            "aggregateByKey",
            "groupByKey",
            "avoid",
            "minimize",
        ]
        found = any(p in content.lower() for p in patterns)
        assert found, "No shuffle optimization discussion found"

    def test_spark_session_creation(self):
        """Demo must create a SparkSession."""
        content = self._read_all_demos()
        patterns = [
            "SparkSession",
            "spark.builder",
            "getOrCreate",
            "SparkConf",
            "SparkContext",
        ]
        found = any(p in content for p in patterns)
        assert found, "No SparkSession creation found"

    def test_python_demo_compiles(self):
        """Python demo files must compile."""
        for fpath in self._find_demo_files():
            if fpath.endswith(".py"):
                result = subprocess.run(
                    ["python", "-m", "py_compile", fpath],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                assert (
                    result.returncode == 0
                ), f"{fpath} failed to compile:\n{result.stderr}"
