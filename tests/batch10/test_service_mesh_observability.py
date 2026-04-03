"""
Test for 'service-mesh-observability' skill — Linkerd2 service mesh observability
Validates that the Agent implemented service mesh observability patterns
including metrics, dashboards, and health checks for linkerd2.
"""

import os
import re

import pytest


class TestServiceMeshObservability:
    """Verify service mesh observability in linkerd2."""

    REPO_DIR = "/workspace/linkerd2"

    def test_prometheus_metrics_defined(self):
        """Prometheus metrics must be defined for service mesh."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".go", ".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"prometheus|Counter|Histogram|Gauge|metrics|request_total|latency", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No Prometheus metrics defined"

    def test_grafana_dashboard_config(self):
        """Grafana dashboard config or reference must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".json", ".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"grafana|dashboard|panels|datasource", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No Grafana dashboard config found"

    def test_golden_signals_metrics(self):
        """Golden signals (latency, traffic, errors, saturation) should be tracked."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".go", ".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"latency|request_duration|response_latency", content, re.IGNORECASE):
                        if re.search(r"error|success|failure|status_code", content, re.IGNORECASE):
                            found = True
                            break
            if found:
                break
        assert found, "Golden signals metrics not found"

    def test_health_check_endpoint(self):
        """Health check endpoint must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".go", ".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"health|healthz|readyz|livez|readiness|liveness", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No health check endpoint found"

    def test_distributed_tracing(self):
        """Distributed tracing support must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".go", ".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"trace|tracing|span|jaeger|zipkin|opentelemetry|opencensus", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No distributed tracing found"

    def test_service_topology_or_map(self):
        """Service topology or service map should be available."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".go", ".yaml", ".yml", ".json")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"topology|service.map|graph|dependency|edges|namespace", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No service topology found"

    def test_alerting_rules(self):
        """Alerting rules for service mesh must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml", ".rules")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"alert:|alerting|PrometheusRule|AlertmanagerConfig", content):
                        found = True
                        break
            if found:
                break
        assert found, "No alerting rules found"

    def test_sli_or_slo_definition(self):
        """SLI or SLO definitions should exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".go", ".yaml", ".yml", ".json")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"SLI|SLO|error.budget|service.level|success.rate|availability", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No SLI/SLO definitions found"

    def test_proxy_metrics(self):
        """Proxy-level metrics should be collected."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".go", ".rs", ".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"proxy|inbound|outbound|tcp_|connection|request_total", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No proxy metrics found"

    def test_tap_or_debug_capability(self):
        """Tap or debug capability for live traffic inspection."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".go", ".rs")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Tt]ap|debug|inspect|live.*traffic|pcap", content):
                        found = True
                        break
            if found:
                break
        assert found, "No tap or debug capability found"
