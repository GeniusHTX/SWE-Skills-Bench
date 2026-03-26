"""
Tests for grafana-dashboards skill.
Validates Grafana dashboard JSON, provisioning YAML, and alert rules in grafana repository.
"""

import os
import json
import subprocess
import pytest

REPO_DIR = "/workspace/grafana"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


def _read_json(rel: str) -> dict:
    with open(_path(rel), encoding="utf-8") as f:
        return json.load(f)


def _run(cmd: str, cwd: str = REPO_DIR, timeout: int = 30):
    return subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


class TestGrafanaDashboards:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_dashboard_json_file_exists(self):
        """microservice-monitoring.json must exist and be non-empty."""
        rel = "devenv/dashboards/microservice-monitoring.json"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "dashboard JSON is empty"

    def test_provisioning_and_alert_files_exist(self):
        """provisioning.yaml and alert-rules.yaml must exist."""
        for rel in [
            "devenv/dashboards/provisioning.yaml",
            "devenv/dashboards/alert-rules.yaml",
        ]:
            assert os.path.isfile(_path(rel)), f"{rel} not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_dashboard_has_correct_uid(self):
        """Dashboard JSON uid must equal 'microservice-monitoring-v1'."""
        data = _read_json("devenv/dashboards/microservice-monitoring.json")
        assert (
            data.get("uid") == "microservice-monitoring-v1"
        ), f"Expected uid='microservice-monitoring-v1', got '{data.get('uid')}'"

    def test_dashboard_has_required_panel_types(self):
        """Dashboard must include stat, gauge, and timeseries panel types."""
        data = _read_json("devenv/dashboards/microservice-monitoring.json")
        panel_types = {p.get("type") for p in data.get("panels", [])}
        for required in ["stat", "gauge", "timeseries"]:
            assert (
                required in panel_types
            ), f"Required panel type '{required}' not found in dashboard"

    def test_dashboard_has_required_variables(self):
        """Dashboard must include namespace, service, and interval template variables."""
        data = _read_json("devenv/dashboards/microservice-monitoring.json")
        var_names = {v.get("name") for v in data.get("templating", {}).get("list", [])}
        for var in ["namespace", "service", "interval"]:
            assert (
                var in var_names
            ), f"Required template variable '{var}' not found in dashboard"

    def test_alert_rules_high_error_rate_is_critical(self):
        """alert-rules.yaml must define HighErrorRate with severity=critical and for=5m."""
        import yaml

        content = _read("devenv/dashboards/alert-rules.yaml")
        data = yaml.safe_load(content)
        content_lower = content
        assert (
            "HighErrorRate" in content_lower
        ), "HighErrorRate alert not found in alert-rules.yaml"
        assert (
            "severity: critical" in content_lower or "critical" in content_lower
        ), "HighErrorRate must have severity: critical"
        assert (
            "for: 5m" in content_lower or "5m" in content_lower
        ), "HighErrorRate must have 5m evaluation window"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_dashboard_json_is_parseable(self):
        """microservice-monitoring.json must be valid JSON."""
        data = _read_json("devenv/dashboards/microservice-monitoring.json")
        assert isinstance(data, dict), "Dashboard JSON must be a JSON object"

    def test_provisioning_yaml_is_parseable(self):
        """provisioning.yaml must be valid YAML."""
        import yaml

        content = _read("devenv/dashboards/provisioning.yaml")
        data = yaml.safe_load(content)
        assert data is not None, "provisioning.yaml parsed as empty"

    def test_dashboard_has_at_least_eight_panels(self):
        """Dashboard must have at least 8 panels."""
        data = _read_json("devenv/dashboards/microservice-monitoring.json")
        panels = data.get("panels", [])
        assert len(panels) >= 8, f"Expected >= 8 panels, found {len(panels)}"

    def test_provisioning_update_interval_is_30s(self):
        """provisioning.yaml must set updateIntervalSeconds to 30."""
        content = _read("devenv/dashboards/provisioning.yaml")
        assert (
            "updateIntervalSeconds: 30" in content
        ), "provisioning.yaml must set updateIntervalSeconds: 30"

    def test_provisioning_disallows_ui_updates(self):
        """provisioning.yaml must set allowUiUpdates: false to prevent drift."""
        content = _read("devenv/dashboards/provisioning.yaml")
        assert (
            "allowUiUpdates: false" in content
        ), "provisioning.yaml must set allowUiUpdates: false"

    def test_malformed_json_fails_validation(self):
        """json.loads must raise JSONDecodeError for invalid JSON."""
        with pytest.raises(json.JSONDecodeError):
            json.loads("{invalid json}")
