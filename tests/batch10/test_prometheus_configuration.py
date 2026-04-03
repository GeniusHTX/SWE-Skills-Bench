"""
Test for 'prometheus-configuration' skill — Prometheus monitoring configuration
Validates that the Agent created Prometheus configuration including scrape configs,
alerting rules, and recording rules.
"""

import os
import re

import pytest


class TestPrometheusConfiguration:
    """Verify Prometheus monitoring configuration."""

    REPO_DIR = "/workspace/prometheus"

    def test_prometheus_yml_exists(self):
        """prometheus.yml or prometheus.yaml must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("prometheus.yml", "prometheus.yaml"):
                    found = True
                    break
            if found:
                break
        assert found, "prometheus.yml not found"

    def test_scrape_configs_defined(self):
        """scrape_configs must be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"scrape_configs:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No scrape_configs defined"

    def test_global_scrape_interval(self):
        """Global scrape interval must be configured."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"scrape_interval:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No global scrape interval configured"

    def test_alerting_rules(self):
        """Alerting rules must be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml", ".rules")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"alert:|alerting:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No alerting rules defined"

    def test_recording_rules(self):
        """Recording rules should be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml", ".rules")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"record:|recording:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No recording rules defined"

    def test_job_name_in_scrape(self):
        """Scrape configs must have job_name."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"job_name:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No job_name in scrape configs"

    def test_targets_defined(self):
        """Scrape targets must be defined (static_configs or service discovery)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"static_configs:|targets:|kubernetes_sd_configs:|consul_sd_configs:|file_sd_configs:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No scrape targets defined"

    def test_rule_groups(self):
        """Rule files must use groups structure."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml", ".rules")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"groups:", content) and re.search(r"rules:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No rule groups found"

    def test_alert_has_expr(self):
        """Alert rules must have an expr field."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml", ".rules")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"alert:", content) and re.search(r"expr:", content):
                        found = True
                        break
            if found:
                break
        assert found, "Alert rules have no expr field"

    def test_alert_has_for_duration(self):
        """Alert rules should have a 'for' duration."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml", ".rules")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"alert:", content) and re.search(r"for:", content):
                        found = True
                        break
            if found:
                break
        assert found, "Alert rules have no 'for' duration"

    def test_rule_file_referenced(self):
        """prometheus.yml should reference rule files."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("prometheus.yml", "prometheus.yaml"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"rule_files:", content):
                        found = True
                    break
        assert found, "prometheus.yml does not reference rule_files"
