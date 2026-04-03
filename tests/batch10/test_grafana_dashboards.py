"""
Test for 'grafana-dashboards' skill — RED method Grafana dashboard
Validates that the Agent created a Grafana dashboard JSON with Rate, Error,
and Duration panels, along with a Go validator.
"""

import os
import re

import pytest


class TestGrafanaDashboards:
    """Verify Grafana RED method dashboard and Go validator."""

    REPO_DIR = "/workspace/grafana"

    def test_dashboard_json_exists(self):
        """At least one dashboard JSON file must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".json"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"\"panels\"", content) and re.search(r"\"dashboard\"|\"title\"", content):
                        found = True
                        break
            if found:
                break
        assert found, "No dashboard JSON found"

    def test_rate_panel_exists(self):
        """Dashboard must have a Rate panel."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".json"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Rr]ate|rate\(|requests.*per.*second|throughput", content, re.IGNORECASE):
                        if "panels" in content:
                            found = True
                            break
            if found:
                break
        assert found, "Rate panel not found in dashboard"

    def test_error_panel_exists(self):
        """Dashboard must have an Error panel."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".json"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Ee]rror.*[Rr]ate|error_rate|5xx|errors", content, re.IGNORECASE):
                        if "panels" in content:
                            found = True
                            break
            if found:
                break
        assert found, "Error panel not found in dashboard"

    def test_duration_panel_exists(self):
        """Dashboard must have a Duration/Latency panel."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".json"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Dd]uration|[Ll]atency|histogram_quantile|p99|p95|percentile", content, re.IGNORECASE):
                        if "panels" in content:
                            found = True
                            break
            if found:
                break
        assert found, "Duration/Latency panel not found in dashboard"

    def test_dashboard_has_datasource(self):
        """Dashboard panels must reference a data source."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".json"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"\"datasource\"|\"dataSource\"", content):
                        found = True
                        break
            if found:
                break
        assert found, "No datasource found in dashboard"

    def test_dashboard_uses_prometheus_queries(self):
        """Dashboard should use Prometheus/PromQL queries."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".json"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"\"expr\":|promql|rate\(|histogram_quantile", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No Prometheus queries found in dashboard"

    def test_go_validator_exists(self):
        """Go dashboard validator must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".go"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Vv]alidat|dashboard|[Ll]int", content):
                        found = True
                        break
            if found:
                break
        assert found, "No Go dashboard validator found"

    def test_validator_checks_panels(self):
        """Go validator should check that panels exist in dashboard."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".go"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Pp]anel|\"panels\"", content):
                        if re.search(r"[Vv]alidat|check|assert|error", content, re.IGNORECASE):
                            found = True
                            break
            if found:
                break
        assert found, "Validator does not check panels"

    def test_dashboard_has_template_variables(self):
        """Dashboard should have template variables for filtering."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".json"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"\"templating\"|\"variables\"|\"__name\"|\"\\$", content):
                        found = True
                        break
            if found:
                break
        assert found, "No template variables in dashboard"

    def test_dashboard_version_or_id(self):
        """Dashboard JSON should have a version or uid."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".json"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"\"uid\"|\"version\"|\"id\"", content):
                        if "panels" in content:
                            found = True
                            break
            if found:
                break
        assert found, "Dashboard JSON has no uid/version/id"

    def test_go_test_file_for_validator(self):
        """Go test file for the validator should exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith("_test.go"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Vv]alidat|dashboard", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No Go test file for validator"
