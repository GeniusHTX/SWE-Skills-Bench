"""
Test for 'prometheus-configuration' skill — Prometheus Monitoring Config
Validates prometheus.yml, alert rules, recording rules, scrape configs,
burn rate PromQL, and configuration validation.
"""

import os
import re

import pytest

try:
    import yaml
except ImportError:
    yaml = None


class TestPrometheusConfiguration:
    """Verify Prometheus monitoring configuration."""

    REPO_DIR = "/workspace/prometheus"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_prometheus_yml_exists(self):
        """Verify prometheus.yml configuration file exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f in ("prometheus.yml", "prometheus.yaml"):
                    found = True
                    break
            if found:
                break
        assert found, "No prometheus.yml found"

    def test_alert_rules_exist(self):
        """Verify alert rules file exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if ("alert" in f.lower() or "rule" in f.lower()) and (
                    f.endswith(".yml") or f.endswith(".yaml")
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No alert rules file found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_scrape_interval_15s(self):
        """Verify scrape_interval is configured (e.g. 15s)."""
        prom_file = self._find_prometheus_yml()
        if not prom_file:
            pytest.skip("prometheus.yml not found")
        content = self._read(prom_file)
        assert re.search(
            r"scrape_interval:\s*\d+s", content
        ), "No scrape_interval found"

    def test_burn_rate_rules(self):
        """Verify burn rate alerting (14.4x or multi-window)."""
        rule_files = self._find_rule_files()
        for fpath in rule_files:
            content = self._read(fpath)
            if re.search(r"(burn.?rate|14\.4|multi.?window)", content, re.IGNORECASE):
                return
        pytest.fail("No burn rate alerting rules found")

    def test_recording_rules_exist(self):
        """Verify recording rules are defined."""
        rule_files = self._find_rule_files()
        for fpath in rule_files:
            content = self._read(fpath)
            if re.search(r"record:|recording", content, re.IGNORECASE):
                return
        pytest.fail("No recording rules found")

    def test_scrape_configs_with_jobs(self):
        """Verify scrape_configs define jobs."""
        prom_file = self._find_prometheus_yml()
        if not prom_file:
            pytest.skip("prometheus.yml not found")
        content = self._read(prom_file)
        assert "scrape_configs" in content, "No scrape_configs section"
        assert "job_name" in content, "No job_name in scrape_configs"

    # ── functional_check ────────────────────────────────────────────────────

    def test_yaml_files_valid(self):
        """Verify all Prometheus YAML files parse correctly."""
        if yaml is None:
            pytest.skip("PyYAML not available")
        all_files = [self._find_prometheus_yml()] + self._find_rule_files()
        for fpath in all_files:
            if fpath is None:
                continue
            with open(fpath, "r") as fh:
                try:
                    yaml.safe_load(fh)
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {os.path.basename(fpath)}: {e}")

    def test_rule_files_have_groups(self):
        """Verify rule files define groups with rules."""
        if yaml is None:
            pytest.skip("PyYAML not available")
        rule_files = self._find_rule_files()
        for fpath in rule_files:
            data = self._load_yaml(fpath)
            if data and "groups" in data:
                return
        pytest.fail("No rule file with groups found")

    def test_burn_rate_promql(self):
        """Verify burn rate rules use PromQL expressions."""
        rule_files = self._find_rule_files()
        for fpath in rule_files:
            content = self._read(fpath)
            if re.search(r"expr:", content):
                if re.search(r"(rate|increase|sum|avg)", content):
                    return
        pytest.fail("No PromQL expressions in rule files")

    def test_scrape_interval_positive(self):
        """Verify scrape_interval is a positive duration."""
        prom_file = self._find_prometheus_yml()
        if not prom_file:
            pytest.skip("prometheus.yml not found")
        content = self._read(prom_file)
        m = re.search(r"scrape_interval:\s*(\d+)([smh])", content)
        if m:
            val = int(m.group(1))
            assert val > 0, "scrape_interval must be positive"
        else:
            pytest.skip("scrape_interval format not parseable")

    def test_alert_rules_have_expr(self):
        """Verify alert rules define expr (expression)."""
        rule_files = self._find_rule_files()
        for fpath in rule_files:
            content = self._read(fpath)
            if "alert:" in content:
                assert (
                    "expr:" in content
                ), f"Alert without expr in {os.path.basename(fpath)}"
                return
        pytest.skip("No alert rules to verify")

    def test_no_duplicate_job_names(self):
        """Verify no duplicate job names in scrape_configs."""
        prom_file = self._find_prometheus_yml()
        if not prom_file or yaml is None:
            pytest.skip("prometheus.yml or PyYAML not available")
        data = self._load_yaml(prom_file)
        if not data or "scrape_configs" not in data:
            pytest.skip("No scrape_configs")
        jobs = [
            sc.get("job_name") for sc in data["scrape_configs"] if isinstance(sc, dict)
        ]
        assert len(jobs) == len(set(jobs)), f"Duplicate job names: {jobs}"

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_prometheus_yml(self):
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f in ("prometheus.yml", "prometheus.yaml"):
                    return os.path.join(dirpath, f)
        return None

    def _find_rule_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if (
                    "alert" in f.lower() or "rule" in f.lower() or "record" in f.lower()
                ) and (f.endswith(".yml") or f.endswith(".yaml")):
                    results.append(os.path.join(dirpath, f))
        return results

    def _load_yaml(self, path):
        try:
            with open(path, "r") as fh:
                return yaml.safe_load(fh)
        except (yaml.YAMLError, IOError):
            return None

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
