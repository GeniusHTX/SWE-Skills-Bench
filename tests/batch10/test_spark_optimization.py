"""
Test for 'spark-optimization' skill — Apache Spark optimization patterns
Validates that the Agent implemented Spark optimization patterns including
partitioning, caching, and query tuning in the spark project.
"""

import os
import re

import pytest


class TestSparkOptimization:
    """Verify Apache Spark optimization patterns."""

    REPO_DIR = "/workspace/spark"

    def test_spark_session_configuration(self):
        """SparkSession must be configured."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".scala", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"SparkSession|SparkConf|SparkContext|spark\.builder", content):
                        found = True
                        break
            if found:
                break
        assert found, "No SparkSession configuration found"

    def test_partitioning_configuration(self):
        """Partitioning must be configured."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".scala", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"repartition|coalesce|partitionBy|numPartitions|shuffle\.partitions|HashPartitioner", content):
                        found = True
                        break
            if found:
                break
        assert found, "No partitioning configuration found"

    def test_caching_strategy(self):
        """Caching or persistence strategy must be implemented."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".scala", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"\.cache\(\)|\.persist\(|MEMORY_AND_DISK|StorageLevel|unpersist", content):
                        found = True
                        break
            if found:
                break
        assert found, "No caching strategy found"

    def test_broadcast_join(self):
        """Broadcast join optimization should be used."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".scala", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"broadcast|BroadcastHashJoin|autoBroadcastJoinThreshold|spark\.sql\.autoBroadcast", content):
                        found = True
                        break
            if found:
                break
        assert found, "No broadcast join found"

    def test_serialization_config(self):
        """Serialization must be configured (Kryo, etc)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".scala", ".java", ".conf")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Kk]ryo|serializer|spark\.serializer|KryoSerializer", content):
                        found = True
                        break
            if found:
                break
        assert found, "No serialization configuration found"

    def test_memory_configuration(self):
        """Memory configuration must be tuned."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".scala", ".java", ".conf")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"executor\.memory|driver\.memory|memoryFraction|memoryOverhead|spark\.memory", content):
                        found = True
                        break
            if found:
                break
        assert found, "No memory configuration found"

    def test_data_skew_handling(self):
        """Data skew handling should be addressed."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".scala", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"skew|salting|adaptive|AQE|spark\.sql\.adaptive", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No data skew handling found"

    def test_catalyst_optimizer_usage(self):
        """Catalyst optimizer or explain plan should be used."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".scala", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"explain|Catalyst|LogicalPlan|physicalPlan|optimizedPlan|queryExecution", content):
                        found = True
                        break
            if found:
                break
        assert found, "No Catalyst optimizer usage found"

    def test_predicate_pushdown(self):
        """Predicate pushdown or filter optimization should be implemented."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".scala", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"pushdown|predicate|filter.*before|PushDown|FilterExec", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No predicate pushdown found"

    def test_shuffle_optimization(self):
        """Shuffle optimization must be addressed."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".scala", ".java", ".conf")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"shuffle|ShuffleManager|spark\.shuffle|reduceByKey|aggregateByKey", content):
                        found = True
                        break
            if found:
                break
        assert found, "No shuffle optimization found"
