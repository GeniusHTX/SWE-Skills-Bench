"""
Test for 'distributed-tracing' skill — Distributed Tracing
Validates OpenTelemetry collector config YAML for receivers, processors,
exporters, service pipelines, and tracing configuration.
"""

import os
import re
import glob
import yaml
import pytest


class TestDistributedTracing:
    """Tests for distributed tracing in the opentelemetry-collector repo."""

    REPO_DIR = "/workspace/opentelemetry-collector"

    def _find_collector_config(self):
        """Find the otel-collector-config.yaml file."""
        candidates = [
            os.path.join(self.REPO_DIR, "otel-collector-config.yaml"),
            os.path.join(self.REPO_DIR, "collector", "otel-collector-config.yaml"),
            os.path.join(self.REPO_DIR, "config", "otel-collector-config.yaml"),
            os.path.join(self.REPO_DIR, "examples", "otel-collector-config.yaml"),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        # Fallback: search for any otel-collector-config.yaml
        matches = glob.glob(
            os.path.join(self.REPO_DIR, "**/otel-collector-config.yaml"),
            recursive=True,
        )
        return matches[0] if matches else candidates[0]

    def _load_config(self):
        """Load and parse collector config YAML."""
        path = self._find_collector_config()
        with open(path, "r", errors="ignore") as f:
            return yaml.safe_load(f.read())

    # --- File Path Checks ---

    def test_otel_collector_config_yaml_exists(self):
        """Verifies that otel-collector-config.yaml exists."""
        path = os.path.join(self.REPO_DIR, "otel-collector-config.yaml")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_collector_config_yaml_exists(self):
        """Verifies that collector/otel-collector-config.yaml exists."""
        path = os.path.join(self.REPO_DIR, "collector", "otel-collector-config.yaml")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_config_config_yaml_exists(self):
        """Verifies that config/otel-collector-config.yaml exists."""
        path = os.path.join(self.REPO_DIR, "config", "otel-collector-config.yaml")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_examples_config_yaml_exists(self):
        """Verifies that examples/otel-collector-config.yaml exists."""
        path = os.path.join(self.REPO_DIR, "examples", "otel-collector-config.yaml")
        assert os.path.exists(path), f"Expected file not found: {path}"

    # --- Semantic Checks ---

    def test_sem_config_parseable(self):
        """Collector config is valid YAML."""
        cfg = self._load_config()
        assert isinstance(cfg, dict), "Config is not a valid YAML dict"

    def test_sem_has_required_sections(self):
        """Config has receivers, processors, exporters, and service sections."""
        cfg = self._load_config()
        assert "receivers" in cfg, "Missing 'receivers'"
        assert "processors" in cfg, "Missing 'processors'"
        assert "exporters" in cfg, "Missing 'exporters'"
        assert "service" in cfg, "Missing 'service'"

    def test_sem_has_otlp_receiver(self):
        """Config has 'otlp' receiver."""
        cfg = self._load_config()
        assert "otlp" in cfg["receivers"], "Missing 'otlp' receiver"

    def test_sem_has_batch_processor(self):
        """Config has 'batch' processor."""
        cfg = self._load_config()
        assert "batch" in cfg["processors"], "Missing 'batch' processor"

    def test_sem_has_traces_pipeline(self):
        """Config has 'traces' in service.pipelines."""
        cfg = self._load_config()
        assert "traces" in cfg["service"]["pipelines"], "Missing 'traces' pipeline"

    # --- Functional Checks ---

    def test_func_otlp_has_protocols_or_endpoint(self):
        """OTLP receiver has 'protocols' or 'endpoint' config."""
        cfg = self._load_config()
        otlp_cfg = cfg["receivers"]["otlp"]
        assert (
            "protocols" in otlp_cfg or "endpoint" in otlp_cfg
        ), "OTLP missing protocols or endpoint"

    def test_func_grpc_endpoint_4317(self):
        """OTLP gRPC endpoint is on port 4317."""
        cfg = self._load_config()
        otlp_cfg = cfg["receivers"]["otlp"]
        grpc_endpoint = str(
            otlp_cfg.get("protocols", {}).get("grpc", {}).get("endpoint", "")
        )
        assert "4317" in grpc_endpoint or "4317" in str(
            otlp_cfg
        ), "gRPC endpoint not using port 4317"

    def test_func_batch_has_config(self):
        """Batch processor has send_batch_size or timeout."""
        cfg = self._load_config()
        batch_cfg = cfg["processors"]["batch"]
        assert (
            "send_batch_size" in batch_cfg or "timeout" in batch_cfg
        ), "Batch processor missing send_batch_size and timeout"

    def test_func_traces_pipeline_has_receivers(self):
        """Traces pipeline has at least 1 receiver."""
        cfg = self._load_config()
        traces_pipeline = cfg["service"]["pipelines"]["traces"]
        assert (
            len(traces_pipeline["receivers"]) >= 1
        ), "Traces pipeline has no receivers"

    def test_func_traces_pipeline_has_exporters(self):
        """Traces pipeline has at least 1 exporter."""
        cfg = self._load_config()
        traces_pipeline = cfg["service"]["pipelines"]["traces"]
        assert (
            len(traces_pipeline["exporters"]) >= 1
        ), "Traces pipeline has no exporters"

    def test_func_traces_pipeline_uses_otlp_receiver(self):
        """Traces pipeline uses 'otlp' or 'otlp/grpc' receiver."""
        cfg = self._load_config()
        traces_pipeline = cfg["service"]["pipelines"]["traces"]
        assert (
            "otlp" in traces_pipeline["receivers"]
            or "otlp/grpc" in traces_pipeline["receivers"]
        ), "Traces pipeline doesn't use OTLP receiver"

    def test_func_traces_exporter_type(self):
        """Traces pipeline exporter is jaeger, otlp, or zipkin."""
        cfg = self._load_config()
        traces_pipeline = cfg["service"]["pipelines"]["traces"]
        assert any(
            e
            for e in traces_pipeline["exporters"]
            if "jaeger" in e or "otlp" in e or "zipkin" in e
        ), "No known exporter (jaeger/otlp/zipkin) in traces pipeline"

    def test_func_has_memory_limiter(self):
        """Config has memory_limiter processor."""
        cfg = self._load_config()
        assert cfg["processors"].get(
            "memory_limiter"
        ) is not None or "memory_limiter" in str(
            cfg
        ), "Missing memory_limiter processor"

    def test_func_failure_missing_service_pipelines(self):
        """Failure case: validates service.pipelines section exists."""
        cfg = self._load_config()
        assert "pipelines" in cfg.get(
            "service", {}
        ), "Missing service.pipelines section"
