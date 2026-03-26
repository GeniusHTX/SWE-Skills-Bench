"""
Test for 'spark-optimization' skill — Spark Job Optimization Demo
Validates that the Agent created a Spark optimization demo script
that demonstrates repartitioning, caching, broadcast joins, and
before/after performance comparison.
"""

import os
import re
import subprocess

import pytest


class TestSparkOptimization:
    """Verify Spark optimization demo."""

    REPO_DIR = "/workspace/spark"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    def _find_script(self):
        """Locate the Spark optimization demo script."""
        candidates = [
            "examples/spark_optimization_demo.py",
            "examples/optimization_demo.py",
            "spark_optimization_demo.py",
            "optimization_demo.py",
            "examples/src/main/python/spark_optimization_demo.py",
            "examples/src/main/python/optimization_demo.py",
        ]
        for rel in candidates:
            fpath = os.path.join(self.REPO_DIR, rel)
            if os.path.isfile(fpath):
                return fpath
        # Fallback search
        for root, _dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and "optim" in f.lower():
                    return os.path.join(root, f)
        pytest.fail("Spark optimization demo script not found")

    # ------------------------------------------------------------------
    # L1: File existence and syntax
    # ------------------------------------------------------------------

    def test_demo_script_exists(self):
        """A Spark optimization demo Python script must exist."""
        self._find_script()

    def test_script_compiles(self):
        """Demo script must be syntactically valid Python."""
        script = self._find_script()
        result = subprocess.run(
            ["python", "-m", "py_compile", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_imports_pyspark(self):
        """Script must import PySpark modules."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(
            r"from\s+pyspark|import\s+pyspark", content
        ), "Script does not import pyspark"

    # ------------------------------------------------------------------
    # L1: SparkSession creation
    # ------------------------------------------------------------------

    def test_creates_spark_session(self):
        """Script must create a SparkSession."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [r"SparkSession", r"spark.*builder", r"getOrCreate"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not create a SparkSession"

    # ------------------------------------------------------------------
    # L2: Optimization techniques
    # ------------------------------------------------------------------

    def test_uses_repartitioning(self):
        """Script must demonstrate repartitioning."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"\.repartition\(",
            r"\.coalesce\(",
            r"repartition",
            r"coalesce",
            r"numPartitions",
            r"num_partitions",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not use repartitioning"

    def test_uses_caching(self):
        """Script must demonstrate caching/persistence."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [r"\.cache\(\)", r"\.persist\(", r"StorageLevel", r"\.unpersist\("]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not use caching or persistence"

    def test_uses_broadcast_join(self):
        """Script must demonstrate broadcast joins."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"broadcast",
            r"F\.broadcast",
            r"spark\.sql\.autoBroadcast",
            r"BroadcastHashJoin",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not use broadcast joins"

    # ------------------------------------------------------------------
    # L2: Performance comparison
    # ------------------------------------------------------------------

    def test_measures_timing(self):
        """Script must measure execution time for comparison."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"time\.time",
            r"time\.perf_counter",
            r"timeit",
            r"elapsed",
            r"duration",
            r"start_time",
            r"end_time",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not measure execution timing"

    def test_shows_before_after(self):
        """Script must show before/after performance comparison."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"before",
            r"after",
            r"unoptimized",
            r"optimized",
            r"baseline",
            r"improved",
            r"without.*optim",
            r"with.*optim",
            r"naive",
            r"original",
        ]
        found = sum(1 for p in patterns if re.search(p, content, re.IGNORECASE))
        assert found >= 2, (
            f"Only {found} before/after reference(s) found — "
            "need at least 2 for a meaningful comparison"
        )

    def test_has_sample_data(self):
        """Script must generate or define sample data for benchmarks."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"createDataFrame",
            r"range\(",
            r"read\.csv",
            r"read\.parquet",
            r"toDF\(",
            r"parallelize",
            r"generate.*data",
            r"sample",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not create or load sample data"

    def test_has_main_entry(self):
        """Script must have a __main__ entry point."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(
            r'if\s+__name__\s*==\s*["\']__main__["\']', content
        ), "Script lacks __main__ entry point"

    def test_explain_plans_or_metrics(self):
        """Script should show explain plans or output optimization metrics."""
        script = self._find_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"\.explain\(",
            r"print.*time",
            r"speedup",
            r"improvement",
            r"explain",
            r"metric",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not output explain plans or optimization metrics"
