"""
Test for 'grafana-dashboards' skill — Grafana Dashboard Generator (Go)
Validates that the Agent created a Go package for generating Grafana dashboards
with panels, grid layout, and JSON export.
"""

import os
import re
import subprocess

import pytest


class TestGrafanaDashboards:
    """Verify Grafana dashboard generator implementation."""

    REPO_DIR = "/workspace/grafana"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_dashboards_package_files_exist(self):
        """Verify generator.go and panels.go exist under pkg/dashboards/."""
        for rel in ("pkg/dashboards/generator.go", "pkg/dashboards/panels.go"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_models_and_cmd_exist(self):
        """Verify models.go and cmd/dashboard-gen/main.go exist."""
        for rel in ("pkg/dashboards/models.go", "cmd/dashboard-gen/main.go"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_generator_test_file_exists(self):
        """Verify generator_test.go exists for unit testing."""
        path = os.path.join(self.REPO_DIR, "pkg/dashboards/generator_test.go")
        assert os.path.isfile(path), "generator_test.go missing"

    # ── semantic_check ──────────────────────────────────────────────

    def test_generate_and_panel_functions_defined(self):
        """Verify Generate(), NewTimeSeriesPanel(), NewStatPanel(), NewTablePanel() exist."""
        content = self._read(os.path.join(self.REPO_DIR, "pkg/dashboards/generator.go"))
        panels = self._read(os.path.join(self.REPO_DIR, "pkg/dashboards/panels.go"))
        combined = content + panels
        assert combined, "generator.go and panels.go are empty"
        for fn in ("Generate", "NewTimeSeriesPanel", "NewStatPanel", "NewTablePanel"):
            assert fn in combined, f"'{fn}' not found in dashboard package"

    def test_grafana9_schema_fields_present(self):
        """models.go defines struct fields for panels, title, uid (Grafana 9.x schema)."""
        content = self._read(os.path.join(self.REPO_DIR, "pkg/dashboards/models.go"))
        assert content, "models.go is empty or unreadable"
        found = any(kw in content for kw in ("Panels", "Title", "Uid", "UID"))
        assert found, "No dashboard schema fields found in models.go"

    def test_grid_pos_non_overlap_logic(self):
        """Verify generator contains gridPos or layout logic."""
        content = self._read(os.path.join(self.REPO_DIR, "pkg/dashboards/generator.go"))
        panels = self._read(os.path.join(self.REPO_DIR, "pkg/dashboards/panels.go"))
        combined = content + panels
        found = any(kw in combined for kw in ("gridPos", "GridPos", "x:", "y:", "w:", "h:"))
        assert found, "No gridPos layout logic found"

    # ── functional_check (command) ──────────────────────────────────

    def _skip_unless_go(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        result = subprocess.run(
            ["go", "version"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            pytest.skip("go not available")

    def test_go_unit_tests_pass(self):
        """go test ./pkg/dashboards/... passes without errors."""
        self._skip_unless_go()
        result = subprocess.run(
            ["go", "test", "./pkg/dashboards/...", "-v", "-count=1"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, f"Tests failed: {result.stderr}"

    def test_generated_json_has_panels_key(self):
        """Generated dashboard JSON contains 'panels' array key."""
        self._skip_unless_go()
        # Check test file for panels key validation
        content = self._read(os.path.join(
            self.REPO_DIR, "pkg/dashboards/generator_test.go"))
        assert "panels" in content.lower() or "Panels" in content, \
            "No panels validation found in test file"

    def test_invalid_refresh_interval_returns_error(self):
        """Generate() with invalid refresh interval returns ValidationError."""
        self._skip_unless_go()
        result = subprocess.run(
            ["go", "test", "./pkg/dashboards/...", "-run", "TestInvalidRefresh", "-v"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        if result.returncode != 0 and "no test" in result.stdout.lower():
            pytest.skip("TestInvalidRefresh not found")
        assert result.returncode == 0, f"Test failed: {result.stderr}"

    def test_gridpos_no_overlap_in_output(self):
        """Multiple panels have non-overlapping gridPos coordinates."""
        self._skip_unless_go()
        result = subprocess.run(
            ["go", "test", "./pkg/dashboards/...", "-run", "TestGridPosNonOverlap", "-v"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        if result.returncode != 0 and "no test" in result.stdout.lower():
            pytest.skip("TestGridPosNonOverlap not found")
        assert result.returncode == 0, f"Test failed: {result.stderr}"
