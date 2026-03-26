"""
Test for 'grafana-dashboards' skill — Dashboard Provisioning Validator
Validates that the Agent created a Grafana dashboard JSON validator in Go
with proper validation logic, panel checks, and data source consistency.
"""

import os
import re
import subprocess

import pytest


class TestGrafanaDashboards:
    """Verify Grafana dashboard provisioning validator."""

    REPO_DIR = "/workspace/grafana"
    VALIDATOR_DIR = "pkg/services/provisioning/dashboards"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_validator_go_exists(self):
        """validator.go must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.VALIDATOR_DIR, "validator.go")
        )

    def test_validator_test_exists(self):
        """validator_test.go must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.VALIDATOR_DIR, "validator_test.go")
        )

    # ------------------------------------------------------------------
    # L1: Package and basic structure
    # ------------------------------------------------------------------

    def test_validator_has_package(self):
        """validator.go must declare a package."""
        content = self._read(self.VALIDATOR_DIR, "validator.go")
        assert re.search(r"^package\s+\w+", content, re.MULTILINE)

    def test_test_has_package(self):
        """validator_test.go must declare a package."""
        content = self._read(self.VALIDATOR_DIR, "validator_test.go")
        assert re.search(r"^package\s+\w+", content, re.MULTILINE)

    def test_test_imports_testing(self):
        """validator_test.go must import testing package."""
        content = self._read(self.VALIDATOR_DIR, "validator_test.go")
        assert re.search(
            r'"testing"', content
        ), "Test file does not import testing package"

    # ------------------------------------------------------------------
    # L2: Dashboard validation logic
    # ------------------------------------------------------------------

    def test_validates_required_fields(self):
        """Validator must check for required dashboard fields (title, uid, panels)."""
        content = self._read(self.VALIDATOR_DIR, "validator.go")
        fields = ["title", "uid", "panels"]
        found = sum(1 for f in fields if re.search(rf'"{f}"', content, re.IGNORECASE))
        assert found >= 2, f"Validator only checks {found} of {fields}"

    def test_validates_uid_uniqueness(self):
        """Validator must check UID uniqueness across dashboards."""
        content = self._read(self.VALIDATOR_DIR, "validator.go")
        patterns = [
            r"unique",
            r"duplicate",
            r"uid.*seen",
            r"seen.*uid",
            r"uidMap",
            r"uidSet",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Validator does not check UID uniqueness"

    def test_validates_panel_ids(self):
        """Validator must check that panel IDs are unique and non-negative."""
        content = self._read(self.VALIDATOR_DIR, "validator.go")
        patterns = [r"panel.*[Ii][Dd]", r"panelID", r"panel_id", r"PanelId"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Validator does not check panel IDs"

    # ------------------------------------------------------------------
    # L2: Panel validation
    # ------------------------------------------------------------------

    def test_validates_panel_type(self):
        """Validator must check panel type field."""
        content = self._read(self.VALIDATOR_DIR, "validator.go")
        assert re.search(r'"type"', content), "Validator does not check panel type"

    def test_validates_panel_gridpos(self):
        """Validator must check panel gridPos field."""
        content = self._read(self.VALIDATOR_DIR, "validator.go")
        patterns = [r"gridPos", r"GridPos", r"grid_pos"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Validator does not check panel gridPos"

    def test_validates_gridpos_bounds(self):
        """Validator should check gridPos width (max 24 units)."""
        content = self._read(self.VALIDATOR_DIR, "validator.go")
        patterns = [r"24", r"maxWidth", r"dashboard.*width"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Validator does not check gridPos max width (24)"

    # ------------------------------------------------------------------
    # L2: Data source consistency
    # ------------------------------------------------------------------

    def test_validates_data_source_references(self):
        """Validator must check data source references."""
        content = self._read(self.VALIDATOR_DIR, "validator.go")
        patterns = [r"[Dd]ata[Ss]ource", r"datasource", r"data_source"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Validator does not check data source references"

    def test_allows_variable_datasource(self):
        """Validator must allow variable-based data source references ($datasource)."""
        content = self._read(self.VALIDATOR_DIR, "validator.go")
        patterns = [r"\$datasource", r"variable", r"\$\{", r"starts.*\\$"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Validator does not handle variable data source references"

    def test_allows_mixed_datasource(self):
        """Validator must allow '-- Mixed --' placeholder."""
        content = self._read(self.VALIDATOR_DIR, "validator.go")
        patterns = [r"Mixed", r"mixed", r"-- Mixed --"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Validator does not allow -- Mixed -- data source"

    # ------------------------------------------------------------------
    # L2: Error vs warning distinction
    # ------------------------------------------------------------------

    def test_distinguishes_errors_and_warnings(self):
        """Validation results must distinguish errors from warnings."""
        content = self._read(self.VALIDATOR_DIR, "validator.go")
        has_error = re.search(r"[Ee]rror", content)
        has_warning = re.search(r"[Ww]arning", content)
        assert (
            has_error and has_warning
        ), "Validator does not distinguish between errors and warnings"

    # ------------------------------------------------------------------
    # L2: Tests
    # ------------------------------------------------------------------

    def test_test_file_has_test_functions(self):
        """validator_test.go must define test functions."""
        content = self._read(self.VALIDATOR_DIR, "validator_test.go")
        tests = re.findall(r"func\s+Test\w+", content)
        assert len(tests) >= 2, f"Only {len(tests)} test function(s) — need at least 2"
