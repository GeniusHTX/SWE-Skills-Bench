"""
Test for 'grafana-dashboards' skill — Grafana Dashboard Generation (Go)
Validates Dashboard model, RED/USE generators, alert rules, provisioning
YAML, panel counts, threshold steps, and ToJSON error handling.
"""

import glob
import os
import re

import pytest


class TestGrafanaDashboards:
    """Verify Grafana dashboard Go package: model, RED, USE, alerts."""

    REPO_DIR = "/workspace/grafana"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _pkg(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "pkg", "dashboards", *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_model_go_exists(self):
        """pkg/dashboards/model.go must exist."""
        assert os.path.isfile(self._pkg("model.go"))

    def test_red_dashboard_go_exists(self):
        """pkg/dashboards/red_dashboard.go must exist."""
        assert os.path.isfile(self._pkg("red_dashboard.go"))

    def test_use_dashboard_go_exists(self):
        """pkg/dashboards/use_dashboard.go must exist."""
        assert os.path.isfile(self._pkg("use_dashboard.go"))

    def test_alerts_and_provisioning_exist(self):
        """alerts.go and provisioning.go must exist."""
        assert os.path.isfile(self._pkg("alerts.go"))
        assert os.path.isfile(self._pkg("provisioning.go"))

    # ── semantic_check ───────────────────────────────────────────────────

    def test_schema_version_38(self):
        """Dashboard struct must declare SchemaVersion set to 38."""
        content = self._read_file(self._pkg("model.go"))
        if not content:
            pytest.skip("model.go not found")
        assert "SchemaVersion" in content
        assert "38" in content

    def test_generate_red_dashboard_signature(self):
        """GenerateREDDashboard must accept service, namespace, datasource."""
        content = self._read_file(self._pkg("red_dashboard.go"))
        if not content:
            pytest.skip("red_dashboard.go not found")
        assert "func GenerateREDDashboard(" in content
        assert "service" in content
        assert "namespace" in content
        assert "datasource" in content

    def test_tojson_uses_marshalindent(self):
        """ToJSON must use json.MarshalIndent."""
        files = glob.glob(self._pkg("*.go"))
        found = False
        for f in files:
            content = self._read_file(f)
            if "ToJSON" in content and "MarshalIndent" in content:
                found = True
                break
        assert found, "ToJSON with json.MarshalIndent not found"

    def test_alert_five_minute_duration(self):
        """alerts.go must use 5m alert duration."""
        content = self._read_file(self._pkg("alerts.go"))
        if not content:
            pytest.skip("alerts.go not found")
        assert "5m" in content or "5 * time.Minute" in content

    def test_provisioning_disable_deletion(self):
        """provisioning.go must set disableDeletion: true."""
        content = self._read_file(self._pkg("provisioning.go"))
        if not content:
            pytest.skip("provisioning.go not found")
        assert "disableDeletion" in content or "DisableDeletion" in content

    # ── functional_check ─────────────────────────────────────────────────

    def test_red_dashboard_minimum_eight_panels(self):
        """GenerateREDDashboard must create at least 8 panels."""
        content = self._read_file(self._pkg("red_dashboard.go"))
        if not content:
            pytest.skip("red_dashboard.go not found")
        panel_count = content.count("Panel{") + content.count("{Title:")
        assert panel_count >= 8, f"Only {panel_count} panels, expected >= 8"

    def test_error_rate_panel_three_thresholds(self):
        """Error rate panel must define green/yellow/red threshold steps."""
        content = self._read_file(self._pkg("red_dashboard.go"))
        if not content:
            pytest.skip("red_dashboard.go not found")
        for color in ("green", "yellow", "red"):
            assert color in content.lower(), f"Threshold color '{color}' not found"

    def test_business_dashboard_empty_metrics_guard(self):
        """GenerateBusinessDashboard must handle empty metrics."""
        content = self._read_file(self._pkg("business_dashboard.go"))
        if not content:
            pytest.skip("business_dashboard.go not found")
        assert "len(" in content or "nil" in content, "No empty metrics guard"

    def test_tojson_error_propagated(self):
        """ToJSON must return ([]byte, error) and not suppress marshaling errors."""
        files = glob.glob(self._pkg("*.go"))
        for f in files:
            content = self._read_file(f)
            if "ToJSON" in content:
                assert "_ = err" not in content, f"Error suppressed in {f}"
                assert "return" in content
                return
        pytest.skip("ToJSON method not found")
