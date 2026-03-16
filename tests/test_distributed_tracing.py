"""
Test for 'distributed-tracing' skill — OpenTelemetry Collector Pipeline
Validates that the Agent created a complete collector pipeline config with
receivers, processors, exporters, and pipelines.
"""

import os
import subprocess
import pytest


class TestDistributedTracing:
    """Verify OpenTelemetry Collector pipeline configuration."""

    REPO_DIR = "/workspace/opentelemetry-collector"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_config_yaml_exists(self):
        """examples/pipeline-demo/config.yaml must exist."""
        fpath = os.path.join(self.REPO_DIR, "examples", "pipeline-demo", "config.yaml")
        assert os.path.isfile(fpath), "config.yaml not found"

    def test_readme_exists(self):
        """examples/pipeline-demo/README.md must exist."""
        fpath = os.path.join(self.REPO_DIR, "examples", "pipeline-demo", "README.md")
        assert os.path.isfile(fpath), "README.md not found"

    # ------------------------------------------------------------------
    # L2: YAML structure validation
    # ------------------------------------------------------------------

    def _load_config(self):
        import yaml

        fpath = os.path.join(self.REPO_DIR, "examples", "pipeline-demo", "config.yaml")
        with open(fpath, "r") as f:
            return yaml.safe_load(f)

    def test_config_is_valid_yaml(self):
        """config.yaml must be valid YAML."""
        config = self._load_config()
        assert isinstance(config, dict), "Config must be a YAML mapping"

    def test_receivers_section(self):
        """Config must have receivers section."""
        config = self._load_config()
        assert "receivers" in config, "receivers section missing"
        assert (
            len(config["receivers"]) >= 2
        ), f"Expected >= 2 receivers, got {len(config['receivers'])}"

    def test_otlp_receiver(self):
        """Must include OTLP receiver."""
        config = self._load_config()
        receivers = config.get("receivers", {})
        assert "otlp" in receivers or any(
            "otlp" in k for k in receivers
        ), f"OTLP receiver not found; receivers: {list(receivers.keys())}"

    def test_processors_section(self):
        """Config must have processors section."""
        config = self._load_config()
        assert "processors" in config, "processors section missing"
        assert (
            len(config["processors"]) >= 2
        ), f"Expected >= 2 processors, got {len(config['processors'])}"

    def test_batch_processor(self):
        """Must include batch processor."""
        config = self._load_config()
        processors = config.get("processors", {})
        assert "batch" in processors or any(
            "batch" in k for k in processors
        ), f"batch processor not found; processors: {list(processors.keys())}"

    def test_memory_limiter_processor(self):
        """Must include memory_limiter processor."""
        config = self._load_config()
        processors = config.get("processors", {})
        assert "memory_limiter" in processors or any(
            "memory" in k for k in processors
        ), f"memory_limiter not found; processors: {list(processors.keys())}"

    def test_exporters_section(self):
        """Config must have exporters section."""
        config = self._load_config()
        assert "exporters" in config, "exporters section missing"
        assert (
            len(config["exporters"]) >= 2
        ), f"Expected >= 2 exporters, got {len(config['exporters'])}"

    def test_service_pipelines(self):
        """Config must define service.pipelines."""
        config = self._load_config()
        service = config.get("service", {})
        pipelines = service.get("pipelines", {})
        assert len(pipelines) >= 2, f"Expected >= 2 pipelines, got {len(pipelines)}"

    def test_traces_pipeline(self):
        """Must define a traces pipeline."""
        config = self._load_config()
        pipelines = config.get("service", {}).get("pipelines", {})
        assert (
            "traces" in pipelines
        ), f"traces pipeline not found; pipelines: {list(pipelines.keys())}"
        traces = pipelines["traces"]
        assert "receivers" in traces, "traces pipeline missing receivers"
        assert "exporters" in traces, "traces pipeline missing exporters"

    def test_metrics_pipeline(self):
        """Must define a metrics pipeline."""
        config = self._load_config()
        pipelines = config.get("service", {}).get("pipelines", {})
        assert (
            "metrics" in pipelines
        ), f"metrics pipeline not found; pipelines: {list(pipelines.keys())}"

    def test_readme_explains_components(self):
        """README must explain pipeline components."""
        fpath = os.path.join(self.REPO_DIR, "examples", "pipeline-demo", "README.md")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        components = ["receiver", "processor", "exporter", "pipeline"]
        found = sum(1 for c in components if c in content.lower())
        assert found >= 3, f"README only covers {found}/4 pipeline components"
