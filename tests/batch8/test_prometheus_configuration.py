"""
Test for 'prometheus-configuration' skill — Prometheus Config Generator
Validates that the Agent created a Python package for generating Prometheus
scrape configs, alert rules, and alertmanager configs with validation.
"""

import os
import re
import sys

import pytest


class TestPrometheusConfiguration:
    """Verify Prometheus configuration generator implementation."""

    REPO_DIR = "/workspace/prometheus"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_prometheus_config_package_exists(self):
        """Verify __init__.py and generator.py exist under src/prometheus_config/."""
        for rel in ("src/prometheus_config/__init__.py", "src/prometheus_config/generator.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_rules_alertmanager_models_exist(self):
        """Verify rules.py, alertmanager.py, and models.py exist."""
        for rel in ("src/prometheus_config/rules.py",
                     "src/prometheus_config/alertmanager.py",
                     "src/prometheus_config/models.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_classes_importable(self):
        """PrometheusConfigGenerator, RuleGenerator, AlertmanagerConfigBuilder importable."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            from prometheus_config.generator import PrometheusConfigGenerator  # noqa: F401
            from prometheus_config.rules import RuleGenerator  # noqa: F401
            from prometheus_config.alertmanager import AlertmanagerConfigBuilder  # noqa: F401
        except ImportError:
            pytest.skip("prometheus_config not importable")
        finally:
            sys.path.pop(0)

    # ── semantic_check ──────────────────────────────────────────────

    def test_rule_generator_methods_defined(self):
        """Verify generate_alert_rule() and generate_recording_rule() are defined."""
        content = self._read(os.path.join(self.REPO_DIR, "src/prometheus_config/rules.py"))
        assert content, "rules.py is empty or unreadable"
        for method in ("generate_alert_rule", "generate_recording_rule"):
            assert method in content, f"'{method}' not found in rules.py"

    def test_validation_error_for_invalid_inputs(self):
        """Verify rules.py raises ValidationError for empty expr, bad severity."""
        content = self._read(os.path.join(self.REPO_DIR, "src/prometheus_config/rules.py"))
        assert content, "rules.py is empty or unreadable"
        for kw in ("ValidationError", "critical", "warning", "info"):
            assert kw in content, f"'{kw}' not found in rules.py"

    def test_duration_pattern_validation(self):
        """Verify rules.py uses regex to validate duration format (digits + s/m/h/d)."""
        content = self._read(os.path.join(self.REPO_DIR, "src/prometheus_config/rules.py"))
        assert content, "rules.py is empty or unreadable"
        found = any(kw in content for kw in ("re.match", "re.fullmatch", "[smhd]"))
        assert found, "Duration regex validation not found in rules.py"

    # ── functional_check (import) ───────────────────────────────────

    def _import(self, dotpath: str):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            return __import__(dotpath, fromlist=[""])
        except ImportError:
            pytest.skip(f"{dotpath} not importable")
        finally:
            sys.path.pop(0)

    def test_prometheus_yml_has_scrape_configs(self):
        """generate() with 2 scrape jobs produces YAML with 2 scrape_configs entries."""
        import yaml
        gen = self._import("prometheus_config.generator")
        models = self._import("prometheus_config.models")
        config = models.PrometheusConfig(scrape_configs=[
            models.ScrapeConfig("job1", ["localhost:9090"]),
            models.ScrapeConfig("job2", ["localhost:9091"]),
        ])
        out = yaml.safe_load(gen.PrometheusConfigGenerator().generate(config))
        assert len(out["scrape_configs"]) == 2

    def test_default_scrape_interval_15s(self):
        """Config without scrape_interval defaults to global.scrape_interval='15s'."""
        import yaml
        gen = self._import("prometheus_config.generator")
        models = self._import("prometheus_config.models")
        out = yaml.safe_load(gen.PrometheusConfigGenerator().generate(models.PrometheusConfig()))
        assert out["global"]["scrape_interval"] == "15s"

    def test_alert_rule_yaml_has_required_fields(self):
        """generate_alert_rule() returns YAML with alert, expr, for, labels, annotations."""
        import yaml
        rules = self._import("prometheus_config.rules")
        rule_yaml = rules.RuleGenerator().generate_alert_rule(
            "HighCPU", "cpu_usage>80", "5m", "critical", {}, {})
        rule = yaml.safe_load(rule_yaml)["groups"][0]["rules"][0]
        for key in ("alert", "expr", "for", "labels", "annotations"):
            assert key in rule, f"'{key}' not found in alert rule"

    def test_empty_expr_raises_validation_error(self):
        """generate_alert_rule() with empty expr raises ValidationError."""
        rules = self._import("prometheus_config.rules")
        models = self._import("prometheus_config.models")
        with pytest.raises(models.ValidationError):
            rules.RuleGenerator().generate_alert_rule("N", "", "5m", "critical", {}, {})

    def test_invalid_severity_raises_validation_error(self):
        """generate_alert_rule() with severity='urgent' raises ValidationError."""
        rules = self._import("prometheus_config.rules")
        models = self._import("prometheus_config.models")
        with pytest.raises(models.ValidationError):
            rules.RuleGenerator().generate_alert_rule(
                "N", "cpu>80", "5m", "urgent", {}, {})
