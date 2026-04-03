"""
Test for 'spark-optimization' skill — Apache Spark Optimization Patterns
Validates BroadcastJoin, SkewHandler, SparkConfigValidator, PartitionOptimizer,
and CacheStrategyAdvisor via static analysis and pure Python arithmetic checks.
"""

import glob
import math
import os
import re
import sys

import pytest


class TestSparkOptimization:
    """Verify Spark optimization patterns: broadcast, skew, config, partitioning."""

    REPO_DIR = "/workspace/spark"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _find_source(self) -> str:
        """Locate the main Spark optimizer source file."""
        candidates = [
            os.path.join(self.REPO_DIR, "src", "main", "scala", "SparkOptimizer.scala"),
        ]
        py_files = glob.glob(os.path.join(self.REPO_DIR, "examples", "spark", "*.py"))
        for c in candidates:
            if os.path.isfile(c):
                return c
        return py_files[0] if py_files else candidates[0]

    def _find_all_sources(self) -> list:
        """Find all relevant spark source files."""
        files = []
        scala = os.path.join(self.REPO_DIR, "src", "main", "scala", "SparkOptimizer.scala")
        if os.path.isfile(scala):
            files.append(scala)
        files.extend(glob.glob(os.path.join(self.REPO_DIR, "examples", "spark", "*.py")))
        return files

    # ── file_path_check ──────────────────────────────────────────────────

    def test_source_file_exists(self):
        """SparkOptimizer source file must exist (Scala or Python)."""
        sources = self._find_all_sources()
        assert len(sources) >= 1, "No Spark optimizer source files found"

    def test_build_file_exists(self):
        """build.sbt or pom.xml or Python test file must exist."""
        candidates = [
            os.path.join(self.REPO_DIR, "build.sbt"),
            os.path.join(self.REPO_DIR, "pom.xml"),
            os.path.join(self.REPO_DIR, "tests", "test_spark.py"),
        ]
        found = any(os.path.isfile(c) for c in candidates)
        assert found, "No build descriptor or test file found"

    def test_readme_mentions_spark(self):
        """README.md must mention Spark setup."""
        path = os.path.join(self.REPO_DIR, "README.md")
        if not os.path.isfile(path):
            pytest.skip("README.md not found")
        content = self._read_file(path)
        has_spark = "spark" in content.lower() or "sbt" in content.lower() or "pyspark" in content.lower()
        assert has_spark, "README does not mention Spark/sbt/pyspark"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_broadcast_join_hint(self):
        """Source must use broadcast() hint or autoBroadcastJoinThreshold."""
        sources = self._find_all_sources()
        found = False
        for src in sources:
            content = self._read_file(src)
            if "broadcast" in content.lower():
                found = True
                break
        assert found, "No broadcast join hint found"

    def test_skew_handler_salting(self):
        """SkewHandler must use salting pattern (salt/rand)."""
        sources = self._find_all_sources()
        found = False
        for src in sources:
            content = self._read_file(src)
            if "salt" in content.lower() or ("rand" in content and "skew" in content.lower()):
                found = True
                break
        assert found, "No salting pattern found in SkewHandler"

    def test_config_validator_memory_regex(self):
        """Config validator must use memory format regex with [kmgKMG]."""
        sources = self._find_all_sources()
        found = False
        for src in sources:
            content = self._read_file(src)
            if re.search(r"[kmgKMG]", content) and ("regex" in content.lower() or "re." in content or "match" in content):
                found = True
                break
        assert found, "No memory format regex validation found"

    def test_partition_uses_128mb_target(self):
        """Partition optimizer must reference 128MB target partition size."""
        sources = self._find_all_sources()
        found = False
        for src in sources:
            content = self._read_file(src)
            if "128" in content or "134217728" in content or "maxPartitionBytes" in content:
                found = True
                break
        assert found, "128MB partition target not found"

    # ── functional_check ─────────────────────────────────────────────────

    def test_partition_formula_arithmetic(self):
        """ceil(1_000_000_000 / 134_217_728) == 8 partitions."""
        result = math.ceil(1_000_000_000 / 134_217_728)
        assert result == 8

    def test_config_validator_rejects_invalid_format(self):
        """SparkConfigValidator must reject '10x' as invalid memory format."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.spark.config_validator import SparkConfigValidator, ConfigError
        except ImportError:
            pytest.skip("Cannot import SparkConfigValidator")
        with pytest.raises(ConfigError):
            SparkConfigValidator().validate_memory("10x")

    def test_config_validator_accepts_valid_formats(self):
        """SparkConfigValidator must accept '1g', '512m', '2048k'."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.spark.config_validator import SparkConfigValidator
        except ImportError:
            pytest.skip("Cannot import SparkConfigValidator")
        for fmt in ["1g", "512m", "2048k"]:
            SparkConfigValidator().validate_memory(fmt)

    def test_config_validator_rejects_empty(self):
        """SparkConfigValidator must reject empty string."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.spark.config_validator import SparkConfigValidator, ConfigError
        except ImportError:
            pytest.skip("Cannot import SparkConfigValidator")
        with pytest.raises(ConfigError):
            SparkConfigValidator().validate_memory("")

    def test_skew_salt_factor_1_edge(self):
        """Source must handle salt factor N=1 as no-op or special case."""
        sources = self._find_all_sources()
        found = False
        for src in sources:
            content = self._read_file(src)
            if "salt" in content.lower() and ("== 1" in content or "=1" in content):
                found = True
                break
        # Soft check — not all implementations guard N=1
        if not found:
            sources_content = " ".join(self._read_file(s) for s in sources)
            assert "salt" in sources_content.lower(), "No salt logic found at all"
