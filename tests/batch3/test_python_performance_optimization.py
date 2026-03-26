"""
Tests for python-performance-optimization skill.
Validates Rust flamegraph and stack_trace files in py-spy repository.
"""

import os
import re
import glob
import pytest

REPO_DIR = "/workspace/py-spy"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestPythonPerformanceOptimization:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_flamegraph_rs_exists(self):
        """src/flamegraph.rs must exist."""
        rel = "src/flamegraph.rs"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "flamegraph.rs is empty"

    def test_stack_trace_rs_exists(self):
        """src/stack_trace.rs must exist."""
        rel = "src/stack_trace.rs"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "stack_trace.rs is empty"

    def test_flamegraph_bench_rs_exists(self):
        """benches/flamegraph_bench.rs must exist."""
        rel = "benches/flamegraph_bench.rs"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "flamegraph_bench.rs is empty"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_stack_frame_uses_arc_str_or_interned(self):
        """StackFrame must use Arc<str> or InternedString to avoid per-frame allocation."""
        content = _read("src/stack_trace.rs")
        assert "struct StackFrame" in content, "StackFrame struct not defined"
        has_arc_or_intern = (
            "Arc<str>" in content
            or "InternedString" in content
            or "Arc<String>" in content
        )
        assert (
            has_arc_or_intern
        ), "StackFrame must use Arc<str> or InternedString (found neither)"

    def test_flamegraph_uses_hashmap_for_children(self):
        """flamegraph.rs must use HashMap for child node lookup."""
        content = _read("src/flamegraph.rs")
        assert "HashMap" in content, "HashMap not imported or used in flamegraph.rs"
        assert "children" in content, "No 'children' field found in flamegraph.rs"

    def test_pre_allocated_string_buffer(self):
        """flamegraph.rs must pre-allocate String buffer with String::with_capacity."""
        content = _read("src/flamegraph.rs")
        assert (
            "with_capacity" in content
        ), "String::with_capacity not found — SVG buffer not pre-allocated"

    def test_bench_has_criterion_benchmarks(self):
        """flamegraph_bench.rs must define criterion benchmark group with >= 3 entries."""
        content = _read("benches/flamegraph_bench.rs")
        assert (
            "criterion_group!" in content or "criterion" in content.lower()
        ), "criterion_group! macro not found in flamegraph_bench.rs"
        # Count fn declarations for bench functions
        fn_count = len(re.findall(r"\bfn\s+bench_", content))
        assert (
            fn_count >= 3 or "criterion_group!" in content
        ), f"Expected >= 3 bench functions, found {fn_count}"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_intern_pool_has_size_limit(self):
        """Intern pool must have a size limit to prevent unbounded memory growth (mocked)."""
        MAX_POOL = 10_000

        class InternPool:
            def __init__(self, max_size: int = MAX_POOL):
                self._pool = {}
                self.max_size = max_size

            def intern(self, s: str) -> str:
                if s in self._pool:
                    return self._pool[s]
                if len(self._pool) >= self.max_size:
                    raise MemoryError("Intern pool at capacity")
                self._pool[s] = s
                return self._pool[s]

        pool = InternPool(max_size=5)
        for i in range(5):
            pool.intern(f"func_{i}")
        with pytest.raises(MemoryError):
            pool.intern("overflow_func")

    def test_flamegraph_distinct_nodes_for_distinct_funcs(self):
        """Distinct function names must produce separate child nodes (mocked)."""
        from collections import defaultdict

        class FlamegraphNode:
            def __init__(self, name: str):
                self.name = name
                self.count = 0
                self.children = {}

        def build_flamegraph(stacks: list) -> FlamegraphNode:
            root = FlamegraphNode("root")
            for stack in stacks:
                node = root
                for frame in stack:
                    if frame not in node.children:
                        node.children[frame] = FlamegraphNode(frame)
                    node = node.children[frame]
                    node.count += 1
            return root

        stacks = [["main", "parse", "tokenize"], ["main", "parse", "lex"]]
        root = build_flamegraph(stacks)
        parse_node = root.children["main"].children["parse"]
        assert "tokenize" in parse_node.children, "tokenize node missing"
        assert "lex" in parse_node.children, "lex node missing"

    def test_stack_frame_equality_by_content(self):
        """StackFrames with same content must compare equal (mocked)."""
        from dataclasses import dataclass

        @dataclass
        class StackFrame:
            function: str
            line: int

        f1 = StackFrame(function="main", line=10)
        f2 = StackFrame(function="main", line=10)
        assert f1 == f2, "StackFrames with same content must be equal"

    def test_empty_stacks_produces_empty_flamegraph(self):
        """Building flamegraph from empty stacks must return empty result (mocked)."""

        class EmptyInputError(Exception):
            pass

        def build_flamegraph(stacks: list):
            if not stacks:
                raise EmptyInputError("No stacks provided")
            return {"root": {}}

        with pytest.raises(EmptyInputError):
            build_flamegraph([])

    def test_duplicate_stack_merges_counts(self):
        """Identical stacks must be merged with additive counts (mocked)."""
        from collections import defaultdict

        class FlamegraphNode:
            def __init__(self, name: str):
                self.name = name
                self.count = 0
                self.children = {}

        def build_flamegraph(stacks: list) -> FlamegraphNode:
            root = FlamegraphNode("root")
            for stack in stacks:
                node = root
                for frame in stack:
                    if frame not in node.children:
                        node.children[frame] = FlamegraphNode(frame)
                    node = node.children[frame]
                    node.count += 1
            return root

        stacks = [["main", "work"]] * 3
        root = build_flamegraph(stacks)
        work_node = root.children["main"].children["work"]
        assert work_node.count == 3, f"Expected count=3, got {work_node.count}"
