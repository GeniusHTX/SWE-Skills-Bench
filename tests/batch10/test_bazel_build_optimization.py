"""
Test for 'bazel-build-optimization' skill — Bazel Build Optimization
Validates that the Agent optimized Bazel build configuration with WORKSPACE,
BUILD files, graph.py analysis, and config validator.
"""

import os
import re

import pytest


class TestBazelBuildOptimization:
    """Verify Bazel build optimization implementation."""

    REPO_DIR = "/workspace/bazel"

    def test_workspace_file_exists(self):
        """WORKSPACE or WORKSPACE.bazel file must exist."""
        candidates = [
            os.path.join(self.REPO_DIR, "WORKSPACE"),
            os.path.join(self.REPO_DIR, "WORKSPACE.bazel"),
        ]
        assert any(os.path.isfile(p) for p in candidates), (
            "WORKSPACE file not found"
        )

    def test_build_files_exist(self):
        """At least one BUILD or BUILD.bazel file must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("BUILD", "BUILD.bazel"):
                    found = True
                    break
            if found:
                break
        assert found, "No BUILD files found"

    def test_graph_py_exists(self):
        """graph.py dependency analysis module must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "graph.py" or (f.endswith(".py") and "graph" in f.lower()):
                    found = True
                    break
            if found:
                break
        assert found, "graph.py module not found"

    def test_config_validator_exists(self):
        """Config validator module must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and ("config" in f.lower() and "valid" in f.lower()):
                    found = True
                    break
            if found:
                break
        assert found, "Config validator not found"

    def test_build_rule_optimization(self):
        """BUILD files must contain optimized rules (e.g., remote caching, config)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("BUILD", "BUILD.bazel", ".bazelrc"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"remote_cache|disk_cache|--config|optimization", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No build optimization configuration found"

    def test_dependency_visibility_properly_set(self):
        """BUILD files must set visibility appropriately."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("BUILD", "BUILD.bazel"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"visibility\s*=", content):
                        found = True
                        break
            if found:
                break
        assert found, "No visibility settings in BUILD files"

    def test_graph_analysis_detects_cycles(self):
        """graph.py should have cycle detection logic."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and "graph" in f.lower():
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"cycle|circular|topological|DFS|dfs", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "graph.py has no cycle detection"

    def test_bazelrc_optimization_flags(self):
        """.bazelrc should contain optimization flags."""
        bazelrc = os.path.join(self.REPO_DIR, ".bazelrc")
        if not os.path.isfile(bazelrc):
            pytest.skip(".bazelrc not found")
        with open(bazelrc, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"--jobs|--local_cpu|--remote|--disk_cache|--repository_cache", content), (
            ".bazelrc does not contain optimization flags"
        )

    def test_external_dependencies_pinned(self):
        """External dependencies in WORKSPACE should be pinned to specific versions."""
        workspace = None
        for name in ["WORKSPACE", "WORKSPACE.bazel"]:
            path = os.path.join(self.REPO_DIR, name)
            if os.path.isfile(path):
                workspace = path
                break
        if workspace is None:
            pytest.skip("WORKSPACE file not found")
        with open(workspace, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"sha256|commit|tag|version", content), (
            "External deps not pinned in WORKSPACE"
        )

    def test_test_targets_defined(self):
        """BUILD files should define test targets."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("BUILD", "BUILD.bazel"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"_test\(|test_suite\(", content):
                        found = True
                        break
            if found:
                break
        assert found, "No test targets defined in BUILD files"

    def test_config_validator_validates_build_files(self):
        """Config validator should validate BUILD file structure."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and "config" in f.lower() and "valid" in f.lower():
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"BUILD|validate|check|parse", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Config validator does not validate BUILD files"
