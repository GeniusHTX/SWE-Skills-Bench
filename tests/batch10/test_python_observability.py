"""
Test for 'python-observability' skill — OpenTelemetry Python instrumentation
Validates that the Agent implemented observability patterns with
OpenTelemetry in the opentelemetry-python project.
"""

import os
import re

import pytest


class TestPythonObservability:
    """Verify OpenTelemetry Python observability implementation."""

    REPO_DIR = "/workspace/opentelemetry-python"

    def test_tracer_provider_setup(self):
        """TracerProvider must be configured."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"TracerProvider|set_tracer_provider|get_tracer", content):
                        found = True
                        break
            if found:
                break
        assert found, "No TracerProvider setup found"

    def test_meter_provider_setup(self):
        """MeterProvider must be configured for metrics."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"MeterProvider|set_meter_provider|get_meter|create_counter|create_histogram", content):
                        found = True
                        break
            if found:
                break
        assert found, "No MeterProvider setup found"

    def test_span_creation(self):
        """Code must create spans for tracing."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"start_span|start_as_current_span|with tracer", content):
                        found = True
                        break
            if found:
                break
        assert found, "No span creation found"

    def test_exporter_configured(self):
        """An exporter must be configured (OTLP, Jaeger, Zipkin, Console)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"OTLPSpanExporter|JaegerExporter|ZipkinExporter|ConsoleSpanExporter|BatchSpanProcessor", content):
                        found = True
                        break
            if found:
                break
        assert found, "No exporter configured"

    def test_logging_integration(self):
        """Logging should be integrated with OpenTelemetry."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"LoggerProvider|LoggingHandler|log_record|LogExporter|logging", content):
                        found = True
                        break
            if found:
                break
        assert found, "No logging integration found"

    def test_context_propagation(self):
        """Context propagation must be implemented."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"propagat|inject|extract|TraceContextTextMapPropagator|W3C", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No context propagation found"

    def test_span_attributes(self):
        """Spans must set attributes."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"set_attribute|span\.set_attribute|attributes=", content):
                        found = True
                        break
            if found:
                break
        assert found, "No span attributes set"

    def test_metric_instruments(self):
        """Metric instruments (counter, histogram, gauge) must be created."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"create_counter|create_histogram|create_gauge|create_up_down_counter|Counter\(|Histogram\(", content):
                        found = True
                        break
            if found:
                break
        assert found, "No metric instruments created"

    def test_resource_configuration(self):
        """Resource attributes (service.name, etc) must be configured."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"Resource\(|service\.name|SERVICE_NAME|resource=", content):
                        found = True
                        break
            if found:
                break
        assert found, "No resource configuration found"

    def test_otel_import(self):
        """Code must import from opentelemetry."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"from\s+opentelemetry|import\s+opentelemetry", content):
                        found = True
                        break
            if found:
                break
        assert found, "No opentelemetry import found"
