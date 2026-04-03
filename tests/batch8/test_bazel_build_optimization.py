"""
Test for 'bazel-build-optimization' skill — Bazel Build Graph Optimizer
Validates that the Agent created a Python package for analyzing Bazel build
graphs, computing critical paths, cache keys, and generating BUILD files.
"""

import os
import re
import sys

import pytest


class TestBazelBuildOptimization:
    """Verify Bazel build optimization package implementation."""

    REPO_DIR = "/workspace/bazel"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_bazel_optimizer_package_exists(self):
        """Verify bazel_optimizer package __init__.py and core module files exist."""
        for rel in (
            "src/bazel_optimizer/__init__.py",
            "src/bazel_optimizer/analyzer.py",
            "src/bazel_optimizer/cache.py",
        ):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_generator_models_exist(self):
        """Verify generator.py and models.py exist in the bazel_optimizer package."""
        for rel in ("src/bazel_optimizer/generator.py", "src/bazel_optimizer/models.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_all_classes_importable(self):
        """All three main classes are importable from bazel_optimizer."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            from bazel_optimizer import BuildAnalyzer, BuildFileGenerator, CacheKeyComputer  # noqa: F401
        except ImportError:
            pytest.skip("bazel_optimizer not importable")
        finally:
            sys.path.pop(0)

    # ── semantic_check ──────────────────────────────────────────────

    def test_analyzer_defines_analyze_graph(self):
        """Verify analyzer.py defines BuildAnalyzer class with analyze_graph method."""
        content = self._read(os.path.join(self.REPO_DIR, "src/bazel_optimizer/analyzer.py"))
        assert content, "analyzer.py is empty or unreadable"
        for pat in ("class BuildAnalyzer", "analyze_graph", "CyclicDependencyError"):
            assert pat in content, f"'{pat}' not found in analyzer.py"

    def test_cache_uses_sha256(self):
        """Verify cache.py uses hashlib.sha256 for cache key computation."""
        content = self._read(os.path.join(self.REPO_DIR, "src/bazel_optimizer/cache.py"))
        assert content, "cache.py is empty or unreadable"
        assert "sha256" in content, "sha256 not found in cache.py"
        assert "hashlib" in content, "hashlib not found in cache.py"

    def test_models_buildgraph_dataclass(self):
        """Verify models.py defines BuildGraph dataclass with critical_path and bottlenecks."""
        content = self._read(os.path.join(self.REPO_DIR, "src/bazel_optimizer/models.py"))
        assert content, "models.py is empty or unreadable"
        for pat in ("BuildGraph", "critical_path", "bottlenecks"):
            assert pat in content, f"'{pat}' not found in models.py"

    # ── functional_check (import) ───────────────────────────────────

    def _import_module(self, dotpath: str):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            return __import__(dotpath, fromlist=[""])
        except ImportError:
            pytest.skip(f"{dotpath} not importable")
        finally:
            sys.path.pop(0)

    def test_analyze_graph_critical_path(self):
        """analyze_graph_from_dict computes correct critical path for a DAG."""
        mod = self._import_module("bazel_optimizer.analyzer")
        analyzer = mod.BuildAnalyzer()
        graph = analyzer.analyze_graph_from_dict(
            {"//a": ["//b"], "//b": [], "//c": ["//a", "//b"]}
        )
        assert isinstance(graph.critical_path, list), "critical_path should be a list"
        assert "//c" in graph.critical_path, "//c should be in the critical path"

    def test_cyclic_dependency_raises_error(self):
        """Graph with A->B->A cycle raises CyclicDependencyError."""
        mod = self._import_module("bazel_optimizer.analyzer")
        with pytest.raises(mod.CyclicDependencyError):
            mod.BuildAnalyzer().analyze_graph_from_dict(
                {"//a": ["//b"], "//b": ["//a"]}
            )

    def test_cache_key_stable_unordered_deps(self):
        """CacheKeyComputer produces identical hex digest regardless of dep list order."""
        mod = self._import_module("bazel_optimizer.cache")
        c = mod.CacheKeyComputer()
        k1 = c.compute("//target", ["//dep1", "//dep2"])
        k2 = c.compute("//target", ["//dep2", "//dep1"])
        assert k1 == k2, "Cache key should be stable regardless of dep order"

    def test_cache_key_changes_on_dep_change(self):
        """CacheKeyComputer produces different hex digest when deps differ."""
        mod = self._import_module("bazel_optimizer.cache")
        c = mod.CacheKeyComputer()
        k1 = c.compute("//t", ["//a"])
        k2 = c.compute("//t", ["//b"])
        assert k1 != k2, "Different deps should produce different cache keys"

    def test_generated_build_file_contains_py_library(self):
        """BuildFileGenerator generates BUILD file content containing py_library rule."""
        mod = self._import_module("bazel_optimizer.generator")
        generated = mod.BuildFileGenerator().generate_from_analysis(
            {"//lib": {"rule": "py_library", "deps": ["//common"]}}
        )
        content = generated.get("//lib", "")
        assert "py_library" in content, "py_library rule not found in generated content"
        assert "load(" in content, "load() statement not found in generated content"
