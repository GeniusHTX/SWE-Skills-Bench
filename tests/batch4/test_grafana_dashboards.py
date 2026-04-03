"""
Test for 'grafana-dashboards' skill — Grafana Dashboards
Validates dashboard.json for panels, templating variables, UIDs,
PromQL expressions, and panel structure in the grafana repo.
"""

import os
import re
import glob
import json
import pytest


class TestGrafanaDashboards:
    """Tests for Grafana dashboards in the grafana repo."""

    REPO_DIR = "/workspace/grafana"

    def _find_dashboard(self):
        """Find the dashboard.json file."""
        candidates = [
            os.path.join(self.REPO_DIR, "dashboards", "dashboard.json"),
            os.path.join(self.REPO_DIR, "provisioning", "dashboards", "dashboard.json"),
            os.path.join(self.REPO_DIR, "dashboard.json"),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        # Fallback: search
        matches = glob.glob(
            os.path.join(self.REPO_DIR, "**/dashboard.json"), recursive=True
        )
        return matches[0] if matches else candidates[0]

    def _load_dashboard(self):
        """Load and parse dashboard JSON."""
        path = self._find_dashboard()
        with open(path, "r", errors="ignore") as f:
            return json.loads(f.read())

    # --- File Path Checks ---

    def test_dashboards_dashboard_json_exists(self):
        """Verifies that dashboards/dashboard.json exists."""
        path = os.path.join(self.REPO_DIR, "dashboards", "dashboard.json")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_provisioning_dashboard_json_exists(self):
        """Verifies that provisioning/dashboards/dashboard.json exists."""
        path = os.path.join(
            self.REPO_DIR, "provisioning", "dashboards", "dashboard.json"
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_root_dashboard_json_exists(self):
        """Verifies that dashboard.json exists at root."""
        path = os.path.join(self.REPO_DIR, "dashboard.json")
        assert os.path.exists(path), f"Expected file not found: {path}"

    # --- Semantic Checks ---

    def test_sem_dashboard_has_panels(self):
        """Dashboard JSON has 'panels' key."""
        d = self._load_dashboard()
        assert "panels" in d, "Dashboard missing 'panels' key"

    def test_sem_has_templating(self):
        """Dashboard has 'templating' with 'list'."""
        d = self._load_dashboard()
        assert "templating" in d, "Dashboard missing 'templating'"
        assert "list" in d["templating"], "Templating missing 'list'"

    def test_sem_has_uid(self):
        """Dashboard has non-empty 'uid'."""
        d = self._load_dashboard()
        assert "uid" in d and d["uid"] != "", "Dashboard missing or empty 'uid'"

    def test_sem_panel_structure(self):
        """All panels have type, title, gridPos, and id."""
        d = self._load_dashboard()
        for p in d["panels"]:
            for k in ["type", "title", "gridPos", "id"]:
                assert k in p, f"Panel missing '{k}'"

    def test_sem_panel_ids_unique(self):
        """Panel IDs are unique."""
        d = self._load_dashboard()
        ids = [p["id"] for p in d["panels"]]
        assert len(set(ids)) == len(ids), "Panel IDs are not unique"

    # --- Functional Checks ---

    def test_func_at_least_4_panels(self):
        """Dashboard has at least 4 panels."""
        d = self._load_dashboard()
        assert len(d["panels"]) >= 4, f"Only {len(d['panels'])} panels, need >= 4"

    def test_func_has_request_or_rate_panel(self):
        """At least one panel has 'request' or 'rate' in title."""
        d = self._load_dashboard()
        assert any(
            "request" in p["title"].lower() or "rate" in p["title"].lower()
            for p in d["panels"]
        ), "No request/rate panel found"

    def test_func_has_error_panel(self):
        """At least one panel has 'error' in title."""
        d = self._load_dashboard()
        assert any(
            "error" in p["title"].lower() for p in d["panels"]
        ), "No error panel found"

    def test_func_has_latency_or_p99_panel(self):
        """At least one panel has 'latency' or 'p99' in title."""
        d = self._load_dashboard()
        assert any(
            "latency" in p["title"].lower() or "p99" in p["title"].lower()
            for p in d["panels"]
        ), "No latency/p99 panel found"

    def test_func_has_histogram_quantile(self):
        """Panels use 'histogram_quantile(0.99' PromQL expression."""
        d = self._load_dashboard()
        all_exprs = [
            t["expr"] for p in d["panels"] for t in p.get("targets", []) if "expr" in t
        ]
        assert any(
            "histogram_quantile(0.99" in e for e in all_exprs
        ), "No histogram_quantile(0.99) expression found"

    def test_func_has_rate_expression(self):
        """Panels use 'rate(' PromQL expression."""
        d = self._load_dashboard()
        all_exprs = [
            t["expr"] for p in d["panels"] for t in p.get("targets", []) if "expr" in t
        ]
        assert any("rate(" in e for e in all_exprs), "No rate() expression found"

    def test_func_template_variables(self):
        """Templating has environment, service, namespace, or env variable."""
        d = self._load_dashboard()
        template_names = [v["name"] for v in d["templating"]["list"]]
        assert any(
            n in template_names for n in ("environment", "service", "namespace", "env")
        ), "No expected template variable found"

    def test_func_has_refresh(self):
        """Dashboard has 'refresh' setting."""
        d = self._load_dashboard()
        assert d.get("refresh") is not None, "Dashboard missing 'refresh' setting"
