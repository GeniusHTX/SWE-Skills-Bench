"""
Test for 'distributed-tracing' skill — Tail-Based Sampling Processor
Validates that the Agent created a tail-based sampling processor for the
OpenTelemetry Collector with proper Go files, interfaces, and sampling logic.
"""

import os
import re
import subprocess

import pytest


class TestDistributedTracing:
    """Verify OTel Collector tail-based sampling processor."""

    REPO_DIR = "/workspace/opentelemetry-collector"
    PROC_DIR = "processor/tailsamplingprocessor"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_processor_go_exists(self):
        """processor.go must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.PROC_DIR, "processor.go")
        )

    def test_config_go_exists(self):
        """config.go must exist."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, self.PROC_DIR, "config.go"))

    def test_factory_go_exists(self):
        """factory.go must exist."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, self.PROC_DIR, "factory.go"))

    # ------------------------------------------------------------------
    # L1: Go syntax — at minimum verify structures
    # ------------------------------------------------------------------

    def test_processor_has_package(self):
        """processor.go must declare a package."""
        content = self._read(self.PROC_DIR, "processor.go")
        assert re.search(
            r"^package\s+\w+", content, re.MULTILINE
        ), "processor.go missing package declaration"

    def test_config_has_package(self):
        """config.go must declare a package."""
        content = self._read(self.PROC_DIR, "config.go")
        assert re.search(
            r"^package\s+\w+", content, re.MULTILINE
        ), "config.go missing package declaration"

    def test_factory_has_package(self):
        """factory.go must declare a package."""
        content = self._read(self.PROC_DIR, "factory.go")
        assert re.search(
            r"^package\s+\w+", content, re.MULTILINE
        ), "factory.go missing package declaration"

    # ------------------------------------------------------------------
    # L2: Processor interface — ConsumeTraces
    # ------------------------------------------------------------------

    def test_implements_consume_traces(self):
        """processor.go must implement ConsumeTraces."""
        content = self._read(self.PROC_DIR, "processor.go")
        assert re.search(
            r"func\s+\([^)]+\)\s+ConsumeTraces", content
        ), "processor.go does not implement ConsumeTraces method"

    # ------------------------------------------------------------------
    # L2: Sampling policies
    # ------------------------------------------------------------------

    def test_error_sampling_policy(self):
        """Processor must support always-sample-on-error policy."""
        # Check across config and processor files
        texts = []
        for f in ("processor.go", "config.go"):
            texts.append(self._read(self.PROC_DIR, f))
        combined = "\n".join(texts)
        patterns = [r"error", r"status.*error", r"Error", r"StatusCode.*Error"]
        assert any(
            re.search(p, combined) for p in patterns
        ), "No error-based sampling policy found"

    def test_latency_threshold_policy(self):
        """Processor must support duration/latency threshold policy."""
        texts = []
        for f in ("processor.go", "config.go"):
            texts.append(self._read(self.PROC_DIR, f))
        combined = "\n".join(texts)
        patterns = [r"latency", r"duration", r"threshold", r"Duration", r"Latency"]
        assert any(
            re.search(p, combined, re.IGNORECASE) for p in patterns
        ), "No latency threshold sampling policy found"

    def test_probabilistic_policy(self):
        """Processor must support probabilistic sampling."""
        texts = []
        for f in ("processor.go", "config.go"):
            texts.append(self._read(self.PROC_DIR, f))
        combined = "\n".join(texts)
        patterns = [
            r"probabilistic",
            r"Probabilistic",
            r"sample.*rate",
            r"SamplingRate",
            r"probability",
        ]
        assert any(
            re.search(p, combined, re.IGNORECASE) for p in patterns
        ), "No probabilistic sampling policy found"

    # ------------------------------------------------------------------
    # L2: Configuration
    # ------------------------------------------------------------------

    def test_config_has_policies(self):
        """Config must define sampling policies."""
        content = self._read(self.PROC_DIR, "config.go")
        patterns = [r"Policies", r"Policy", r"policies"]
        assert any(
            re.search(p, content) for p in patterns
        ), "config.go does not define sampling policies"

    def test_config_has_buffer_settings(self):
        """Config must include trace buffer settings."""
        content = self._read(self.PROC_DIR, "config.go")
        patterns = [
            r"[Bb]uffer",
            r"MaxTraces",
            r"max_traces",
            r"buffer_size",
            r"BufferSize",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "config.go does not define buffer settings"

    def test_config_has_timeout(self):
        """Config must include a decision timeout."""
        content = self._read(self.PROC_DIR, "config.go")
        patterns = [r"[Tt]imeout", r"DecisionWait", r"decision_wait", r"timeout"]
        assert any(
            re.search(p, content) for p in patterns
        ), "config.go does not define a decision timeout"

    # ------------------------------------------------------------------
    # L2: Factory registration
    # ------------------------------------------------------------------

    def test_factory_registers_type(self):
        """Factory must register a processor type name."""
        content = self._read(self.PROC_DIR, "factory.go")
        patterns = [
            r"NewFactory",
            r"typeStr",
            r"component\.Type",
            r"processorType",
            r'"tailsampling"',
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "factory.go does not register a processor type"

    # ------------------------------------------------------------------
    # L2: Buffer management
    # ------------------------------------------------------------------

    def test_buffer_eviction_logic(self):
        """Processor must handle buffer eviction of old traces."""
        content = self._read(self.PROC_DIR, "processor.go")
        patterns = [r"evict", r"delete", r"remove", r"cleanup", r"expire", r"purge"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "No buffer eviction/cleanup logic in processor.go"
