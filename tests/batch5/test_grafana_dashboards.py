"""
Test for 'grafana-dashboards' skill — Grafana Dashboard JSON Models
Validates dashboard JSON files with schema version, panels, template
variables, thresholds, and datasource configuration.
"""

import json
import os
import re

import pytest


class TestGrafanaDashboards:
    """Verify Grafana dashboard JSON models."""

    REPO_DIR = "/workspace/grafana"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_dashboard_json_files_exist(self):
        """Verify at least 2 dashboard JSON files exist."""
        json_files = self._find_dashboard_files()
        assert (
            len(json_files) >= 2
        ), f"Expected ≥2 dashboard JSON files, found {len(json_files)}"

    def test_generator_script_exists(self):
        """Verify a dashboard generator/provisioner script exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath or "node_modules" in dirpath:
                continue
            for f in fnames:
                if (
                    "generat" in f.lower()
                    or "provision" in f.lower()
                    or "builder" in f.lower()
                ) and (
                    f.endswith(".py")
                    or f.endswith(".go")
                    or f.endswith(".ts")
                    or f.endswith(".js")
                    or f.endswith(".jsonnet")
                ):
                    found = True
                    break
            if found:
                break
        if not found:
            pytest.skip("No dashboard generator script found (may use manual JSON)")

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_schema_version_gte_30(self):
        """Verify dashboard schemaVersion ≥ 30."""
        json_files = self._find_dashboard_files()
        assert json_files, "No dashboard files"
        for fpath in json_files:
            data = self._load_json(fpath)
            if data and "schemaVersion" in data:
                assert (
                    data["schemaVersion"] >= 30
                ), f"schemaVersion {data['schemaVersion']} < 30 in {os.path.basename(fpath)}"
                return
        pytest.fail("No dashboard with schemaVersion field found")

    def test_panels_count_gte_5(self):
        """Verify dashboard has ≥5 panels."""
        json_files = self._find_dashboard_files()
        assert json_files, "No dashboard files"
        max_panels = 0
        for fpath in json_files:
            data = self._load_json(fpath)
            if data and "panels" in data:
                panel_count = len(data["panels"])
                # Count nested panels in rows
                for p in data["panels"]:
                    if isinstance(p, dict) and "panels" in p:
                        panel_count += len(p["panels"])
                max_panels = max(max_panels, panel_count)
        assert max_panels >= 5, f"Expected ≥5 panels, max found: {max_panels}"

    def test_template_variables_exist(self):
        """Verify dashboard defines template variables."""
        json_files = self._find_dashboard_files()
        assert json_files, "No dashboard files"
        for fpath in json_files:
            data = self._load_json(fpath)
            if data and "templating" in data:
                tpl = data["templating"]
                if isinstance(tpl, dict) and "list" in tpl and len(tpl["list"]) > 0:
                    return
        pytest.fail("No template variables found")

    def test_thresholds_defined(self):
        """Verify panels define thresholds (yellow > 1%, red > 5% or similar)."""
        json_files = self._find_dashboard_files()
        for fpath in json_files:
            data = self._load_json(fpath)
            if not data or "panels" not in data:
                continue
            for panel in data["panels"]:
                if isinstance(panel, dict):
                    content = json.dumps(panel)
                    if "threshold" in content.lower():
                        return
        pytest.fail("No panel thresholds found")

    def test_datasource_uid_prometheus(self):
        """Verify at least one panel uses Prometheus datasource."""
        json_files = self._find_dashboard_files()
        for fpath in json_files:
            content = self._read(fpath)
            if re.search(r"prometheus|Prometheus", content):
                return
        pytest.fail("No Prometheus datasource reference found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_dashboard_json_valid(self):
        """Verify all dashboard JSON files are valid JSON."""
        json_files = self._find_dashboard_files()
        assert json_files, "No dashboard files"
        for fpath in json_files:
            with open(fpath, "r", errors="ignore") as fh:
                try:
                    json.load(fh)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {os.path.basename(fpath)}: {e}")

    def test_panels_have_type(self):
        """Verify all panels specify a type."""
        json_files = self._find_dashboard_files()
        for fpath in json_files:
            data = self._load_json(fpath)
            if not data or "panels" not in data:
                continue
            for panel in data["panels"]:
                if isinstance(panel, dict):
                    assert (
                        "type" in panel or "panels" in panel
                    ), f"Panel missing 'type' in {os.path.basename(fpath)}"
            return
        pytest.fail("No panels to verify")

    def test_panels_have_targets(self):
        """Verify panels have query targets."""
        json_files = self._find_dashboard_files()
        for fpath in json_files:
            data = self._load_json(fpath)
            if not data or "panels" not in data:
                continue
            for panel in data["panels"]:
                if isinstance(panel, dict) and "targets" in panel:
                    return
        pytest.fail("No panel targets/queries found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_dashboard_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath or "node_modules" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".json") and (
                    "dashboard" in f.lower() or "dash" in dirpath.lower()
                ):
                    results.append(os.path.join(dirpath, f))
        return results

    def _load_json(self, path):
        try:
            with open(path, "r", errors="ignore") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, IOError):
            return None

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
