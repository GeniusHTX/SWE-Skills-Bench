"""
Test for 'prometheus-configuration' skill — Multi-Job Scrape Config
Validates that the Agent created a multi-job Prometheus scrape configuration
with proper YAML structure, multiple jobs, relabeling, and service discovery.
"""

import os
import re
import subprocess

import yaml
import pytest


class TestPrometheusConfiguration:
    """Verify multi-job scrape configuration for Prometheus."""

    REPO_DIR = "/workspace/prometheus"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    def _find_config(self):
        """Find the multi-job scrape configuration file."""
        candidates = [
            "documentation/examples/multi_job_scrape.yml",
            "documentation/examples/multi_job_scrape.yaml",
            "examples/multi_job_scrape.yml",
            "examples/multi_job_scrape.yaml",
        ]
        for rel in candidates:
            fpath = os.path.join(self.REPO_DIR, rel)
            if os.path.isfile(fpath):
                return fpath
        # Fallback: search for any multi_job YAML
        for root, _dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if "multi_job" in f and f.endswith((".yml", ".yaml")):
                    return os.path.join(root, f)
        pytest.fail("Multi-job scrape configuration file not found")

    def _load_config(self):
        """Load and parse the YAML configuration."""
        path = self._find_config()
        with open(path, "r", errors="ignore") as fh:
            return yaml.safe_load(fh)

    # ------------------------------------------------------------------
    # L1: YAML validity and top-level structure
    # ------------------------------------------------------------------

    def test_config_file_exists(self):
        """multi_job_scrape.yml must exist."""
        self._find_config()

    def test_valid_yaml(self):
        """Configuration file must be valid YAML."""
        path = self._find_config()
        with open(path, "r", errors="ignore") as fh:
            try:
                data = yaml.safe_load(fh)
            except yaml.YAMLError as exc:
                pytest.fail(f"Invalid YAML: {exc}")
        assert isinstance(data, dict), "Top-level YAML must be a mapping"

    def test_has_global_settings(self):
        """Configuration must define global settings."""
        data = self._load_config()
        assert "global" in data, "Missing 'global' section"
        g = data["global"]
        assert "scrape_interval" in g, "Missing global scrape_interval"
        assert "evaluation_interval" in g, "Missing global evaluation_interval"

    def test_has_external_labels(self):
        """Global section must include external_labels."""
        data = self._load_config()
        g = data.get("global", {})
        assert "external_labels" in g, "Missing external_labels in global"
        assert isinstance(
            g["external_labels"], dict
        ), "external_labels must be a mapping"

    # ------------------------------------------------------------------
    # L1: Scrape jobs
    # ------------------------------------------------------------------

    def test_defines_at_least_three_jobs(self):
        """Configuration must define at least three scrape jobs."""
        data = self._load_config()
        jobs = data.get("scrape_configs", [])
        assert len(jobs) >= 3, f"Only {len(jobs)} scrape job(s) — need at least 3"

    def test_jobs_have_names(self):
        """Each scrape job must have a job_name."""
        data = self._load_config()
        jobs = data.get("scrape_configs", [])
        for i, job in enumerate(jobs):
            assert "job_name" in job, f"Job #{i} missing job_name"

    def test_jobs_have_scrape_settings(self):
        """At least one job should have custom scrape_interval or metrics_path."""
        data = self._load_config()
        jobs = data.get("scrape_configs", [])
        has_custom = any("scrape_interval" in j or "metrics_path" in j for j in jobs)
        assert has_custom, "No job defines custom scrape_interval or metrics_path"

    # ------------------------------------------------------------------
    # L2: Service discovery
    # ------------------------------------------------------------------

    def test_uses_static_config(self):
        """At least one job must use static_configs."""
        data = self._load_config()
        jobs = data.get("scrape_configs", [])
        has_static = any("static_configs" in j for j in jobs)
        assert has_static, "No job uses static_configs"

    def test_uses_dynamic_service_discovery(self):
        """At least one job must use a dynamic SD mechanism."""
        data = self._load_config()
        jobs = data.get("scrape_configs", [])
        sd_keys = [
            "file_sd_configs",
            "dns_sd_configs",
            "kubernetes_sd_configs",
            "consul_sd_configs",
            "ec2_sd_configs",
            "http_sd_configs",
        ]
        has_sd = any(any(k in j for k in sd_keys) for j in jobs)
        assert has_sd, "No job uses a dynamic service discovery mechanism"

    # ------------------------------------------------------------------
    # L2: Relabeling
    # ------------------------------------------------------------------

    def test_uses_relabel_configs(self):
        """At least one job must include relabel_configs."""
        data = self._load_config()
        jobs = data.get("scrape_configs", [])
        has_relabel = any("relabel_configs" in j for j in jobs)
        assert has_relabel, "No job uses relabel_configs"

    def test_relabel_includes_actions(self):
        """Relabeling rules should include keep/drop, replace, or labelmap."""
        data = self._load_config()
        jobs = data.get("scrape_configs", [])
        actions = set()
        for job in jobs:
            for rule in job.get("relabel_configs", []):
                if "action" in rule:
                    actions.add(rule["action"])
        # default action is 'replace' if no action specified
        if not actions:
            # check if there are rules at all
            has_rules = any(job.get("relabel_configs") for job in jobs)
            if has_rules:
                actions.add("replace")
        assert len(actions) >= 1, "Relabeling rules have no actions"

    # ------------------------------------------------------------------
    # L2: Test data fixture
    # ------------------------------------------------------------------

    def test_test_fixture_exists(self):
        """Test fixture multi_job.good.yml should exist."""
        candidates = [
            "config/testdata/multi_job.good.yml",
            "config/testdata/multi_job.good.yaml",
        ]
        found = any(os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        if not found:
            # Not strictly required, just check it's referenced
            config_text = (
                self._read(os.path.relpath(self._find_config(), self.REPO_DIR))
                if False
                else ""
            )
            pytest.skip("Test fixture not created (optional)")

    def test_distinct_job_types(self):
        """Jobs should target distinct service types."""
        data = self._load_config()
        jobs = data.get("scrape_configs", [])
        names = [j.get("job_name", "") for j in jobs]
        assert len(set(names)) == len(names), f"Duplicate job names: {names}"
