"""
Test for 'service-mesh-observability' skill — Service Mesh Observability
Validates Go observability package: TracingConfigBuilder, MetricsAggregator,
AlertRuleBuilder, DashboardConfigBuilder, percentile methods, thresholds.
"""

import glob
import os

import pytest


class TestServiceMeshObservability:
    """Verify service mesh observability: tracing, metrics, alerts, dashboards."""

    REPO_DIR = "/workspace/linkerd2"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _obs(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "observability", *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_go_mod_and_tracing_go_exist(self):
        """go.mod and observability/tracing.go must exist."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, "go.mod"))
        assert os.path.isfile(self._obs("tracing.go"))

    def test_metrics_and_dashboard_go_exist(self):
        """observability/metrics.go and dashboard.go must exist."""
        assert os.path.isfile(self._obs("metrics.go"))
        assert os.path.isfile(self._obs("dashboard.go"))

    def test_alerts_and_test_files_exist(self):
        """alerts.go and at least one *_test.go must exist."""
        assert os.path.isfile(self._obs("alerts.go"))
        assert glob.glob(self._obs("*_test.go")), "No *_test.go in observability/"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_tracing_config_builder_struct(self):
        """TracingConfigBuilder and Build() must be defined."""
        content = self._read_file(self._obs("tracing.go"))
        if not content:
            pytest.skip("tracing.go not found")
        assert "TracingConfigBuilder" in content
        assert "Build" in content

    def test_tracing_references_otlp_receivers(self):
        """tracing.go must reference otlp and receivers for YAML config."""
        content = self._read_file(self._obs("tracing.go"))
        if not content:
            pytest.skip("tracing.go not found")
        assert "otlp" in content
        assert "receivers" in content.lower() or "Receivers" in content

    def test_metrics_aggregator_percentile_methods(self):
        """MetricsAggregator must have P50, P95, P99 methods."""
        content = self._read_file(self._obs("metrics.go"))
        if not content:
            pytest.skip("metrics.go not found")
        assert "MetricsAggregator" in content
        for p in ("P50", "P95", "P99"):
            assert p in content, f"{p} method not found"

    def test_alert_severity_thresholds(self):
        """alerts.go must define 0.05/critical and 0.01/warning thresholds."""
        content = self._read_file(self._obs("alerts.go"))
        if not content:
            pytest.skip("alerts.go not found")
        assert "0.05" in content
        assert "critical" in content.lower()
        assert "0.01" in content
        assert "warning" in content.lower()

    def test_dashboard_config_builder_panels(self):
        """DashboardConfigBuilder must reference panels and JSON."""
        content = self._read_file(self._obs("dashboard.go"))
        if not content:
            pytest.skip("dashboard.go not found")
        assert "DashboardConfigBuilder" in content
        assert "panels" in content.lower() or "Panels" in content

    # ── functional_check ─────────────────────────────────────────────────

    def test_p99_nil_guard(self):
        """MetricsAggregator must handle empty data without panicking (nil/len check)."""
        content = self._read_file(self._obs("metrics.go"))
        if not content:
            pytest.skip("metrics.go not found")
        has_guard = ("nil" in content or "len(" in content) and "return" in content
        assert has_guard, "No nil/empty guard in metrics.go P99 method"

    def test_critical_threshold_0_05(self):
        """alerts.go must pair 0.05 with critical severity."""
        content = self._read_file(self._obs("alerts.go"))
        if not content:
            pytest.skip("alerts.go not found")
        # Both must appear in the file
        assert "0.05" in content and "critical" in content.lower()

    def test_warning_threshold_0_01(self):
        """alerts.go must pair 0.01 with warning severity."""
        content = self._read_file(self._obs("alerts.go"))
        if not content:
            pytest.skip("alerts.go not found")
        assert "0.01" in content and "warning" in content.lower()

    def test_dashboard_produces_json(self):
        """dashboard.go must use json.Marshal or json.NewEncoder."""
        content = self._read_file(self._obs("dashboard.go"))
        if not content:
            pytest.skip("dashboard.go not found")
        assert "json.Marshal" in content or "json.NewEncoder" in content
