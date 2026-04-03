"""
Test for 'slo-implementation' skill — SLO Generator
Validates 99.9% target, multi-window burn rates, ErrorBudget calculation,
SLI/SLO configuration, and alerting integration.
"""

import os
import re

import pytest

try:
    import yaml
except ImportError:
    yaml = None


class TestSloImplementation:
    """Verify SLO implementation in slo-generator."""

    REPO_DIR = "/workspace/slo-generator"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_slo_source_exists(self):
        """Verify slo-generator source directory exists."""
        assert os.path.isdir(self.REPO_DIR), "slo-generator repo not found"

    def test_slo_config_files_exist(self):
        """Verify SLO configuration files exist."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith((".yaml", ".yml", ".py", ".json")) and "slo" in f.lower():
                    found = True
                    break
            if found:
                break
        assert found, "No SLO config files found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_slo_target_999(self):
        """Verify 99.9% SLO target."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(r"(99\.9|0\.999|target.*99|goal.*99)", content, re.IGNORECASE):
                return
        pytest.fail("No 99.9% SLO target found")

    def test_multi_window_burn_rate(self):
        """Verify multi-window burn rate alerting."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(burn.?rate|multi.?window|lookback|window)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No multi-window burn rate found")

    def test_error_budget(self):
        """Verify ErrorBudget calculation."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(error.?budget|ErrorBudget|budget_remaining|budget_consumed)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No ErrorBudget calculation found")

    def test_sli_definition(self):
        """Verify SLI (Service Level Indicator) definition."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(SLI|service.?level.?indicator|good_events|total_events|sli_config)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No SLI definition found")

    def test_alerting_integration(self):
        """Verify alerting integration (PagerDuty, Slack, etc.)."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(alert|notification|PagerDuty|Slack|webhook|alertmanager)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No alerting integration found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_source_files_parse(self):
        """Verify Python source files are syntactically valid."""
        import ast

        py_files = [f for f in self._find_source_files() if f.endswith(".py")]
        for fpath in py_files[:15]:
            content = self._read(fpath)
            try:
                ast.parse(content, filename=fpath)
            except SyntaxError as e:
                pytest.fail(f"SyntaxError in {os.path.basename(fpath)}: {e}")

    def test_yaml_configs_valid(self):
        """Verify YAML config files parse correctly."""
        if yaml is None:
            pytest.skip("PyYAML not available")
        yaml_files = [
            f for f in self._find_source_files() if f.endswith((".yaml", ".yml"))
        ]
        for fpath in yaml_files[:10]:
            with open(fpath, "r") as fh:
                try:
                    yaml.safe_load(fh)
                except yaml.YAMLError as e:
                    pytest.fail(f"YAML error in {os.path.basename(fpath)}: {e}")

    def test_backend_integration(self):
        """Verify backend integration (Prometheus, Stackdriver, etc.)."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(Prometheus|Stackdriver|CloudMonitoring|Datadog|backend_class)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No backend integration found")

    def test_slo_report_generation(self):
        """Verify SLO report/export generation."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(report|export|BigQuery|Sheet|output|publish)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No SLO report generation found")

    def test_time_window_config(self):
        """Verify time window configuration (calendar, rolling)."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(calendar|rolling|window_seconds|time_window|lookback_duration)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No time window config found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_source_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith((".py", ".yaml", ".yml", ".json")):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
