"""Test file for the prometheus-configuration skill.

This suite validates Prometheus, recording rules, alerting rules,
and alertmanager configuration files for k8s monitoring.
"""

from __future__ import annotations

import pathlib
import re

import pytest
import yaml


class TestPrometheusConfiguration:
    """Verify Prometheus k8s-monitoring configuration."""

    REPO_DIR = "/workspace/prometheus"

    PROMETHEUS_YML = "documentation/examples/k8s-monitoring/prometheus.yml"
    RECORDING_RULES_YML = "documentation/examples/k8s-monitoring/recording_rules.yml"
    ALERTING_RULES_YML = "documentation/examples/k8s-monitoring/alerting_rules.yml"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    def _parse_yaml(self, relative: str) -> dict:
        text = self._read_text(relative)
        return yaml.safe_load(text)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_documentation_examples_k8s_monitoring_prometheus_yml_exists(
        self,
    ):
        """Verify prometheus.yml exists and is non-empty."""
        self._assert_non_empty_file(self.PROMETHEUS_YML)

    def test_file_path_documentation_examples_k8s_monitoring_recording_rules_yml_ex(
        self,
    ):
        """Verify recording_rules.yml exists and is non-empty."""
        self._assert_non_empty_file(self.RECORDING_RULES_YML)

    def test_file_path_documentation_examples_k8s_monitoring_alerting_rules_yml_exi(
        self,
    ):
        """Verify alerting_rules.yml exists and is non-empty."""
        self._assert_non_empty_file(self.ALERTING_RULES_YML)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_prometheus_yml_has_global_scrape_interval_15s_and_evaluation(
        self,
    ):
        """prometheus.yml has global scrape_interval: 15s and evaluation_interval: 15s."""
        data = self._parse_yaml(self.PROMETHEUS_YML)
        g = data.get("global", {})
        assert g.get("scrape_interval") == "15s", "Expected global scrape_interval: 15s"
        assert (
            g.get("evaluation_interval") == "15s"
        ), "Expected global evaluation_interval: 15s"

    def test_semantic_prometheus_yml_references_recording_rules_yml_and_alerting_r(
        self,
    ):
        """prometheus.yml references recording_rules.yml and alerting_rules.yml in rule_files."""
        data = self._parse_yaml(self.PROMETHEUS_YML)
        rule_files = data.get("rule_files", [])
        joined = " ".join(str(f) for f in rule_files)
        assert (
            "recording_rules" in joined
        ), "rule_files should reference recording_rules.yml"
        assert (
            "alerting_rules" in joined
        ), "rule_files should reference alerting_rules.yml"

    def test_semantic_kubernetes_pods_job_has_relabel_config_for_prometheus_io_scr(
        self,
    ):
        """kubernetes-pods job has relabel_config for prometheus.io/scrape annotation."""
        data = self._parse_yaml(self.PROMETHEUS_YML)
        scrape_configs = data.get("scrape_configs", [])
        pods_job = None
        for sc in scrape_configs:
            if "pod" in sc.get("job_name", "").lower():
                pods_job = sc
                break
        assert pods_job is not None, "kubernetes-pods scrape job not found"
        relabels = str(pods_job.get("relabel_configs", []))
        assert (
            "prometheus.io/scrape" in relabels
        ), "kubernetes-pods job should have prometheus.io/scrape relabel config"

    def test_semantic_recording_rules_group_named_k8s_aggregations(self):
        """Recording rules group named k8s_aggregations."""
        data = self._parse_yaml(self.RECORDING_RULES_YML)
        groups = data.get("groups", [])
        names = [g.get("name", "") for g in groups]
        assert any(
            "k8s_aggregations" in n for n in names
        ), "Expected recording rules group named k8s_aggregations"

    def test_semantic_namespace_http_error_rate_5m_expression_uses_rate_and_code_5(
        self,
    ):
        """namespace_http_error_rate_5m expression uses rate and code=~'5..'."""
        text = self._read_text(self.RECORDING_RULES_YML)
        assert re.search(
            r"namespace.http.error.rate", text
        ), "Expected namespace_http_error_rate recording rule"
        assert re.search(r"rate\s*\(", text), "Expression should use rate() function"
        assert re.search(r"code.*5\.\.", text) or re.search(
            r"5\.\.|5xx", text
        ), "Expression should filter 5xx status codes"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases)
    # ------------------------------------------------------------------

    def test_functional_all_4_yaml_files_parse_as_valid_yaml(self):
        """All YAML files parse as valid YAML."""
        for rel in (
            self.PROMETHEUS_YML,
            self.RECORDING_RULES_YML,
            self.ALERTING_RULES_YML,
        ):
            data = self._parse_yaml(rel)
            assert data is not None, f"{rel} did not parse as valid YAML"
        # Also check alertmanager.yml if present
        am = self._repo_path("documentation/examples/k8s-monitoring/alertmanager.yml")
        if am.is_file():
            data = yaml.safe_load(am.read_text(encoding="utf-8", errors="ignore"))
            assert data is not None, "alertmanager.yml did not parse as valid YAML"

    def test_functional_prometheus_yml_has_exactly_4_scrape_configs_jobs(self):
        """prometheus.yml has exactly 4 scrape_configs jobs."""
        data = self._parse_yaml(self.PROMETHEUS_YML)
        scrape_configs = data.get("scrape_configs", [])
        assert (
            len(scrape_configs) == 4
        ), f"Expected 4 scrape_configs, got {len(scrape_configs)}"

    def test_functional_recording_rules_yml_has_6_recording_rules(self):
        """recording_rules.yml has 6 recording rules."""
        data = self._parse_yaml(self.RECORDING_RULES_YML)
        groups = data.get("groups", [])
        total_rules = sum(len(g.get("rules", [])) for g in groups)
        assert total_rules == 6, f"Expected 6 recording rules, got {total_rules}"

    def test_functional_alerting_rules_yml_has_6_alert_definitions(self):
        """alerting_rules.yml has 6 alert definitions."""
        data = self._parse_yaml(self.ALERTING_RULES_YML)
        groups = data.get("groups", [])
        total_alerts = sum(
            len([r for r in g.get("rules", []) if "alert" in r]) for g in groups
        )
        assert total_alerts == 6, f"Expected 6 alert definitions, got {total_alerts}"

    def test_functional_alertmanager_yml_has_route_receivers_and_inhibit_rules_secti(
        self,
    ):
        """alertmanager.yml has route, receivers, and inhibit_rules sections."""
        am_path = self._repo_path(
            "documentation/examples/k8s-monitoring/alertmanager.yml"
        )
        assert am_path.is_file(), "alertmanager.yml should exist"
        data = yaml.safe_load(am_path.read_text(encoding="utf-8", errors="ignore"))
        for section in ("route", "receivers", "inhibit_rules"):
            assert section in data, f"alertmanager.yml missing section: {section}"
