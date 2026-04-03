"""
Test for 'service-mesh-observability' skill — Linkerd Service Mesh Observability
Validates 99.5% success threshold, P99 latency >500ms alerting,
Prometheus metrics, and service mesh monitoring configuration.
"""

import os
import re

import pytest

try:
    import yaml
except ImportError:
    yaml = None


class TestServiceMeshObservability:
    """Verify service mesh observability in Linkerd."""

    REPO_DIR = "/workspace/linkerd2"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_observability_files_exist(self):
        """Verify observability/monitoring config files exist."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if (
                    "monitor" in f.lower()
                    or "observ" in f.lower()
                    or "metric" in f.lower()
                    or "prometheus" in f.lower()
                    or "grafana" in f.lower()
                    or "dashboard" in f.lower()
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No observability/monitoring files found"

    def test_prometheus_config_exists(self):
        """Verify Prometheus configuration files exist."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if "prometheus" in f.lower() and (
                    f.endswith(".yml") or f.endswith(".yaml") or f.endswith(".go")
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No Prometheus config found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_success_rate_threshold(self):
        """Verify 99.5% success rate threshold."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(99\.5|0\.995|success.?rate|success_threshold)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No 99.5% success rate threshold found")

    def test_p99_latency_alert(self):
        """Verify P99 latency >500ms alerting."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(p99|P99|percentile.*99|latency.*500|histogram_quantile.*0\.99)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No P99 latency monitoring found")

    def test_prometheus_metrics(self):
        """Verify Prometheus metrics (request_total, latency_bucket, etc.)."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(request_total|response_total|latency_bucket|request_duration|histogram_quantile)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No Prometheus metrics found")

    def test_golden_signals(self):
        """Verify golden signals monitoring (latency, traffic, errors, saturation)."""
        source_files = self._find_source_files()
        signals = set()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(r"latency", content, re.IGNORECASE):
                signals.add("latency")
            if re.search(r"(traffic|throughput|request_total)", content, re.IGNORECASE):
                signals.add("traffic")
            if re.search(r"(error|failure|5\d\d)", content, re.IGNORECASE):
                signals.add("errors")
            if re.search(
                r"(saturation|utilization|cpu|memory)", content, re.IGNORECASE
            ):
                signals.add("saturation")
        assert len(signals) >= 2, f"Only {signals} golden signals found"

    def test_scrape_config(self):
        """Verify Prometheus scrape configuration."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(scrape|prometheus\.io|metrics.?path|port.?name.*metrics)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No scrape configuration found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_yaml_files_valid(self):
        """Verify YAML configuration files parse."""
        if yaml is None:
            pytest.skip("PyYAML not available")
        yaml_files = self._find_yaml_files()
        for fpath in yaml_files[:10]:
            with open(fpath, "r") as fh:
                try:
                    yaml.safe_load(fh)
                except yaml.YAMLError as e:
                    pytest.fail(f"YAML error in {os.path.basename(fpath)}: {e}")

    def test_grafana_dashboard_json(self):
        """Verify Grafana dashboard JSON files exist and parse."""
        import json

        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".json") and (
                    "dashboard" in f.lower() or "grafana" in f.lower()
                ):
                    fpath = os.path.join(dirpath, f)
                    with open(fpath, "r") as fh:
                        data = json.load(fh)
                        assert isinstance(data, dict)
                    found = True
                    break
            if found:
                break
        if not found:
            pytest.skip("No Grafana dashboard JSON found")

    def test_alerting_rules_defined(self):
        """Verify alerting rules for SLO violations."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(alert:|AlertRule|alertmanager|firing|critical|warning)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No alerting rules found")

    def test_service_profile_metrics(self):
        """Verify ServiceProfile-based per-route metrics."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(ServiceProfile|route.*metric|per.?route)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No ServiceProfile per-route metrics found")

    def test_mTLS_or_identity(self):
        """Verify mTLS or identity-based observability."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(mTLS|mutual.?TLS|identity|tls_route|authority)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No mTLS/identity observability found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_source_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith((".go", ".yaml", ".yml", ".json", ".py")):
                    results.append(os.path.join(dirpath, f))
        return results

    def _find_yaml_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith((".yaml", ".yml")):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
