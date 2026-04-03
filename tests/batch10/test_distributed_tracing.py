"""
Test for 'distributed-tracing' skill — OpenTelemetry Collector tail-sampling processor
Validates that the Agent implemented a tail-sampling processor in Go for
the OpenTelemetry Collector.
"""

import os
import re

import pytest


class TestDistributedTracing:
    """Verify OpenTelemetry tail-sampling processor implementation."""

    REPO_DIR = "/workspace/opentelemetry-collector"

    def test_tail_sampling_processor_directory(self):
        """Tail-sampling processor directory must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for d in dirs:
                if "tailsampling" in d.lower() or "tail_sampling" in d.lower() or "tail-sampling" in d.lower():
                    found = True
                    break
            if found:
                break
        assert found, "Tail-sampling processor directory not found"

    def test_processor_go_file_exists(self):
        """A Go file implementing the processor must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "tailsampling" in root.lower() or "tail_sampling" in root.lower():
                for f in files:
                    if f.endswith(".go") and "processor" in f.lower():
                        found = True
                        break
            if found:
                break
        assert found, "Processor Go file not found in tail-sampling directory"

    def test_config_go_file_exists(self):
        """Config struct for the processor must be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "tailsampling" in root.lower() or "tail_sampling" in root.lower():
                for f in files:
                    if f.endswith(".go"):
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            content = fh.read()
                        if re.search(r"type\s+Config\s+struct", content):
                            found = True
                            break
            if found:
                break
        assert found, "Config struct not found"

    def test_factory_function_exists(self):
        """NewFactory or createDefaultConfig function must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "tailsampling" in root.lower() or "tail_sampling" in root.lower():
                for f in files:
                    if f.endswith(".go"):
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            content = fh.read()
                        if re.search(r"func\s+(NewFactory|createDefaultConfig|newFactory)", content):
                            found = True
                            break
            if found:
                break
        assert found, "Factory function not found"

    def test_sampling_policy_defined(self):
        """At least one sampling policy must be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "tailsampling" in root.lower() or "tail_sampling" in root.lower():
                for f in files:
                    if f.endswith(".go"):
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            content = fh.read()
                        if re.search(r"[Pp]olicy|[Ss]ampling[Rr]ule|[Ss]ampler", content):
                            found = True
                            break
            if found:
                break
        assert found, "No sampling policy defined"

    def test_trace_decision_logic(self):
        """Processor must implement trace sampling decision logic."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "tailsampling" in root.lower() or "tail_sampling" in root.lower():
                for f in files:
                    if f.endswith(".go"):
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            content = fh.read()
                        if re.search(r"[Dd]ecision|[Ss]ampled|[Nn]ot[Ss]ampled|shouldSample|Evaluate", content):
                            found = True
                            break
            if found:
                break
        assert found, "No trace decision logic found"

    def test_span_processing(self):
        """Processor must handle spans (ConsumeTraces or processSpan)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "tailsampling" in root.lower() or "tail_sampling" in root.lower():
                for f in files:
                    if f.endswith(".go"):
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            content = fh.read()
                        if re.search(r"ConsumeTraces|processSpan|ProcessTraces|pdata\.Traces", content):
                            found = True
                            break
            if found:
                break
        assert found, "No span processing found"

    def test_error_handling(self):
        """Processor must include error handling."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "tailsampling" in root.lower() or "tail_sampling" in root.lower():
                for f in files:
                    if f.endswith(".go"):
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            content = fh.read()
                        if re.search(r"if\s+err\s*!=\s*nil|errors\.(New|Wrap)|fmt\.Errorf", content):
                            found = True
                            break
            if found:
                break
        assert found, "No error handling found"

    def test_test_file_exists(self):
        """Unit test file for the processor must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "tailsampling" in root.lower() or "tail_sampling" in root.lower():
                for f in files:
                    if f.endswith("_test.go"):
                        found = True
                        break
            if found:
                break
        assert found, "No _test.go file found for processor"

    def test_latency_or_error_based_policy(self):
        """Should include latency-based or error-based sampling policy."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "tailsampling" in root.lower() or "tail_sampling" in root.lower():
                for f in files:
                    if f.endswith(".go"):
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            content = fh.read()
                        if re.search(r"[Ll]atency|[Dd]uration|[Ee]rror.*[Pp]olicy|status.*error|StatusCode", content):
                            found = True
                            break
            if found:
                break
        assert found, "No latency-based or error-based sampling policy found"

    def test_component_type_registration(self):
        """Processor component type must be registered."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "tailsampling" in root.lower() or "tail_sampling" in root.lower():
                for f in files:
                    if f.endswith(".go"):
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            content = fh.read()
                        if re.search(r"component\.Type|typeStr|\"tail_sampling\"|processorhelper", content):
                            found = True
                            break
            if found:
                break
        assert found, "Processor component type not registered"
