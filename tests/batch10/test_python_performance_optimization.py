"""
Test for 'python-performance-optimization' skill — Python profiling with py-spy
Validates that the Agent implemented Python performance optimization patterns
using py-spy or related profiling tools.
"""

import os
import re

import pytest


class TestPythonPerformanceOptimization:
    """Verify Python performance optimization patterns."""

    REPO_DIR = "/workspace/py-spy"

    def test_profiler_integration(self):
        """Profiler integration must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".rs", ".toml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"profil|py.spy|cProfile|profile|perf", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No profiler integration found"

    def test_sampling_mechanism(self):
        """Sampling mechanism for profiling must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".rs")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"sampl|stack.*trace|frame|callstack|backtrace", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No sampling mechanism found"

    def test_flame_graph_or_visualization(self):
        """Flame graph or visualization output must be supported."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".rs", ".md")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"flamegraph|flame.graph|svg|speedscope|visualization", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No flame graph support found"

    def test_process_attachment(self):
        """Profiler must be able to attach to a running process."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".rs")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"pid|process|attach|--pid|ProcessId", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No process attachment found"

    def test_output_format(self):
        """Profiler must support output formats."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".rs", ".md")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"output|format|--output|--format|json|svg|raw", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No output format support found"

    def test_duration_or_rate_config(self):
        """Profiler must support duration or sampling rate configuration."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".rs")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"duration|rate|interval|frequency|--duration|--rate|sampling_rate", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No duration or rate configuration found"

    def test_thread_support(self):
        """Profiler should support multi-threaded applications."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".rs")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"thread|Thread|GIL|gil|ThreadId", content):
                        found = True
                        break
            if found:
                break
        assert found, "No thread support found"

    def test_cargo_toml_exists(self):
        """Cargo.toml must exist for the Rust-based profiler."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "Cargo.toml" in files:
                found = True
                break
        assert found, "Cargo.toml not found"

    def test_python_process_inspection(self):
        """Profiler must inspect Python process internals."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".rs")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"PyInterpreterState|PyFrameObject|_PyRuntime|python.*version|interp", content):
                        found = True
                        break
            if found:
                break
        assert found, "No Python process inspection found"

    def test_error_reporting(self):
        """Profiler must report errors appropriately."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".rs")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"Error|error|Err\(|eprintln|warn|anyhow", content):
                        found = True
                        break
            if found:
                break
        assert found, "No error reporting found"
