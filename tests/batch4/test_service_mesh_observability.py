"""
Test for 'service-mesh-observability' skill — Service Mesh Observability
Validates YAML/JSON files in linkerd2 repo for Prometheus configs,
alerting rules, Grafana dashboards, and service mesh metrics.
"""

import os
import re
import glob
import json
import yaml
import pytest


class TestServiceMeshObservability:
    """Tests for service mesh observability in the linkerd2 repo."""

    REPO_DIR = "/workspace/linkerd2"

    def _load_yaml_docs(self):
        """Load all YAML documents from the repo."""
        all_docs = []
        for f in glob.glob(os.path.join(self.REPO_DIR, "**/*.yaml"), recursive=True):
            try:
                content = open(f, errors="ignore").read()
                for d in yaml.safe_load_all(content):
                    if d:
                        all_docs.append(d)
            except Exception:
                continue
        return all_docs

    def _load_dashboards(self):
        """Load Grafana dashboard JSON files."""
        json_files = glob.glob(os.path.join(self.REPO_DIR, "**/*.json"), recursive=True)
        dashboards = []
        for f in json_files:
            try:
                data = json.loads(open(f, errors="ignore").read())
                if "dashboard" in f.lower() or (
                    isinstance(data, dict) and data.get("panels") is not None
                ):
                    dashboards.append(data)
            except Exception:
                continue
        return dashboards

    # --- File Path Checks ---

    def test_yaml_exists(self):
        """Verifies that YAML files exist in the repo."""
        yamls = glob.glob(os.path.join(self.REPO_DIR, "**/*.yaml"), recursive=True)
        assert len(yamls) > 0, "No YAML files found"

    def test_json_exists(self):
        """Verifies that JSON files exist in the repo."""
        jsons = glob.glob(os.path.join(self.REPO_DIR, "**/*.json"), recursive=True)
        assert len(jsons) > 0, "No JSON files found"

    # --- Semantic Checks ---

    def test_sem_load_yaml_docs(self):
        """YAML documents can be loaded."""
        yaml_docs = self._load_yaml_docs()
        assert len(yaml_docs) > 0, "No YAML documents loaded"

    def test_sem_json_files_found(self):
        """JSON files can be found."""
        json_files = glob.glob(os.path.join(self.REPO_DIR, "**/*.json"), recursive=True)
        assert len(json_files) > 0, "No JSON files found"

    def test_sem_dashboards_found(self):
        """Grafana dashboard JSON files can be found."""
        dashboards = self._load_dashboards()
        assert len(dashboards) > 0, "No dashboard JSON files found"

    # --- Functional Checks ---

    def test_func_has_service_mesh_references(self):
        """YAML docs reference linkerd, istio, or envoy."""
        yaml_docs = self._load_yaml_docs()
        assert any(
            "linkerd" in str(d).lower()
            or "istio" in str(d).lower()
            or "envoy" in str(d).lower()
            for d in yaml_docs
        ), "No linkerd/istio/envoy references found"

    def test_func_has_prometheus_config(self):
        """Has Prometheus ConfigMap or ServiceMonitor."""
        yaml_docs = self._load_yaml_docs()
        prom_configs = [
            d
            for d in yaml_docs
            if d.get("kind") == "ConfigMap" and "prometheus" in str(d).lower()
        ]
        has_service_monitor = any(d.get("kind") == "ServiceMonitor" for d in yaml_docs)
        assert (
            len(prom_configs) >= 1 or has_service_monitor
        ), "No Prometheus ConfigMap or ServiceMonitor found"

    def test_func_has_alert_rules(self):
        """Has PrometheusRule or alert ConfigMap."""
        yaml_docs = self._load_yaml_docs()
        alert_docs = [
            d
            for d in yaml_docs
            if d.get("kind") in ("PrometheusRule", "ConfigMap")
            and "alert" in str(d).lower()
        ]
        assert len(alert_docs) >= 1, "No alerting rules found"

    def test_func_has_mesh_metrics(self):
        """YAML docs reference linkerd_, istio_requests, or envoy_cluster metrics."""
        yaml_docs = self._load_yaml_docs()
        assert any(
            "linkerd_" in str(d)
            or "istio_requests" in str(d)
            or "envoy_cluster" in str(d)
            for d in yaml_docs
        ), "No mesh metrics (linkerd_/istio_requests/envoy_cluster) found"

    def test_func_grafana_dashboard_exists(self):
        """At least one Grafana dashboard JSON found."""
        dashboards = self._load_dashboards()
        grafana_dash = dashboards[0] if dashboards else None
        assert grafana_dash is not None, "No Grafana dashboard found"

    def test_func_dashboard_has_panels(self):
        """Grafana dashboard has at least 4 panels."""
        dashboards = self._load_dashboards()
        assert len(dashboards) > 0, "No dashboards found"
        grafana_dash = dashboards[0]
        assert (
            len(grafana_dash.get("panels", [])) >= 4
        ), "Dashboard has fewer than 4 panels"

    def test_func_dashboard_has_rate_panels(self):
        """Dashboard has panels with 'success', 'error', or 'rate' in title."""
        dashboards = self._load_dashboards()
        assert len(dashboards) > 0, "No dashboards found"
        grafana_dash = dashboards[0]
        panel_titles = [
            p.get("title", "").lower() for p in grafana_dash.get("panels", [])
        ]
        assert any(
            "success" in t or "error" in t or "rate" in t for t in panel_titles
        ), "No success/error/rate panels found"

    def test_func_dashboard_has_latency_panels(self):
        """Dashboard has panels with 'latency' or 'p99' in title."""
        dashboards = self._load_dashboards()
        assert len(dashboards) > 0, "No dashboards found"
        grafana_dash = dashboards[0]
        panel_titles = [
            p.get("title", "").lower() for p in grafana_dash.get("panels", [])
        ]
        assert any(
            "latency" in t or "p99" in t for t in panel_titles
        ), "No latency/p99 panels found"
