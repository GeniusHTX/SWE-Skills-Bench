"""
Test for 'prometheus-configuration' skill — Prometheus Monitoring Setup
Validates that the Agent created proper Prometheus configuration with
scrape targets, alert rules, and alertmanager integration.
"""

import os

import pytest
import yaml


class TestPrometheusConfiguration:
    """Verify Prometheus monitoring configuration."""

    REPO_DIR = "/workspace/prometheus"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _find_prometheus_yml(self):
        for candidate in ["prometheus.yml", "config/prometheus.yml"]:
            p = os.path.join(self.REPO_DIR, candidate)
            if os.path.exists(p):
                return p
        return None

    def _find_alert_rules(self):
        for candidate in ["alert_rules.yml", "rules/alert_rules.yml"]:
            p = os.path.join(self.REPO_DIR, candidate)
            if os.path.exists(p):
                return p
        return None

    def _load_config(self):
        path = self._find_prometheus_yml()
        return yaml.safe_load(open(path).read())

    def _load_alert_config(self):
        path = self._find_alert_rules()
        return yaml.safe_load(open(path).read())

    def _all_rules(self):
        alert_config = self._load_alert_config()
        return [r for g in alert_config["groups"] for r in g["rules"]]

    def _find_rule(self, name):
        for r in self._all_rules():
            if r.get("alert") == name:
                return r
        return None

    # ---- file_path_check ----

    def test_prometheus_yml_exists(self):
        """Verifies prometheus.yml exists."""
        assert self._find_prometheus_yml() is not None, "prometheus.yml not found"

    def test_config_prometheus_yml_exists(self):
        """Verifies config/prometheus.yml exists."""
        path = os.path.join(self.REPO_DIR, "config/prometheus.yml")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_alert_rules_yml_exists(self):
        """Verifies alert_rules.yml exists."""
        assert self._find_alert_rules() is not None, "alert_rules.yml not found"

    def test_rules_alert_rules_yml_exists(self):
        """Verifies rules/alert_rules.yml exists."""
        path = os.path.join(self.REPO_DIR, "rules/alert_rules.yml")
        assert os.path.exists(path), f"Expected file not found: {path}"

    # ---- semantic_check ----

    def test_sem_config_valid_yaml(self):
        """Verifies prometheus.yml has global and scrape_configs."""
        config = self._load_config()
        assert "global" in config, "'global' key missing"
        assert "scrape_configs" in config, "'scrape_configs' key missing"

    def test_sem_rule_files(self):
        """Verifies rule_files has at least 2 entries."""
        config = self._load_config()
        assert "rule_files" in config, "'rule_files' key missing"
        assert (
            len(config["rule_files"]) >= 2
        ), f"Expected >= 2 rule_files, got {len(config['rule_files'])}"

    def test_sem_alerting_configured(self):
        """Verifies alerting section exists."""
        config = self._load_config()
        assert "alerting" in config, "'alerting' key missing"

    def test_sem_alert_groups(self):
        """Verifies alert_rules.yml has groups (edge case)."""
        alert_config = self._load_alert_config()
        assert "groups" in alert_config, "'groups' key missing in alert_rules"

    def test_sem_alert_rule_keys(self):
        """Verifies all alert rules have required keys."""
        for rule in self._all_rules():
            for key in ["alert", "expr"]:
                assert key in rule, f"Alert rule missing '{key}' key"

    def test_sem_severity_labels(self):
        """Verifies all alert labels have severity field."""
        for rule in self._all_rules():
            labels = rule.get("labels", {})
            assert (
                "severity" in labels
            ), f"Alert '{rule.get('alert')}' missing 'severity' label"

    # ---- functional_check ----

    def test_func_high_error_rate_rule(self):
        """Verifies HighErrorRate rule exists (failure scenario)."""
        rule = self._find_rule("HighErrorRate")
        assert rule is not None, "HighErrorRate alert rule not found"

    def test_func_service_down_rule(self):
        """Verifies ServiceDown rule exists."""
        rule = self._find_rule("ServiceDown")
        assert rule is not None, "ServiceDown alert rule not found"

    def test_func_high_latency_rule(self):
        """Verifies HighLatencyP99 or HighLatency rule exists."""
        rules = self._all_rules()
        names = [r.get("alert", "") for r in rules]
        assert any("HighLatency" in n for n in names), "No HighLatency rule found"

    def test_func_high_error_rate_expr(self):
        """Verifies HighErrorRate expr contains rate and threshold (failure)."""
        rule = self._find_rule("HighErrorRate")
        assert rule is not None, "HighErrorRate not found"
        expr = rule["expr"]
        assert "rate" in expr, "HighErrorRate expr missing 'rate'"
        assert "0.05" in expr or "5" in expr, "HighErrorRate expr missing threshold"

    def test_func_service_down_expr(self):
        """Verifies ServiceDown expr uses 'up' and '== 0'."""
        rule = self._find_rule("ServiceDown")
        assert rule is not None, "ServiceDown not found"
        expr = rule["expr"]
        assert "up" in expr, "ServiceDown expr missing 'up'"
        assert "== 0" in expr, "ServiceDown expr missing '== 0'"

    def test_func_high_latency_expr(self):
        """Verifies HighLatency expr uses histogram_quantile."""
        rules = self._all_rules()
        latency_rule = None
        for r in rules:
            if "HighLatency" in r.get("alert", ""):
                latency_rule = r
                break
        assert latency_rule is not None, "No HighLatency rule found"
        expr = latency_rule["expr"]
        assert (
            "histogram_quantile" in expr or "quantile" in expr
        ), "HighLatency expr missing histogram_quantile"

    def test_func_scrape_configs_count(self):
        """Verifies at least 3 scrape jobs configured."""
        config = self._load_config()
        scrape_configs = config["scrape_configs"]
        assert (
            len(scrape_configs) >= 3
        ), f"Expected >= 3 scrape jobs, got {len(scrape_configs)}"

    def test_func_scrape_job_structure(self):
        """Verifies each scrape job has job_name and targets config."""
        config = self._load_config()
        for job in config["scrape_configs"]:
            assert "job_name" in job, "Scrape job missing 'job_name'"
            assert (
                "static_configs" in job or "kubernetes_sd_configs" in job
            ), f"Job '{job['job_name']}' missing targets configuration"
