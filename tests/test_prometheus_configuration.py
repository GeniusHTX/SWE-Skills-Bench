"""
Test for 'prometheus-configuration' skill — Prometheus Configuration
Validates that the Agent created a multi-job scrape configuration example with
relabeling rules and added config parsing tests.
"""

import os
import subprocess
import pytest

from _dependency_utils import ensure_go_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_go_dependencies(TestPrometheusConfiguration.REPO_DIR)


class TestPrometheusConfiguration:
    """Verify Prometheus multi-job scrape configuration."""

    REPO_DIR = "/workspace/prometheus"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_config_example_exists(self):
        """documentation/examples/multi-job-prometheus.yml must exist."""
        fpath = os.path.join(
            self.REPO_DIR, "documentation", "examples", "multi-job-prometheus.yml"
        )
        assert os.path.isfile(fpath), "multi-job-prometheus.yml not found"

    def test_config_test_exists(self):
        """config/config_test.go must exist."""
        fpath = os.path.join(self.REPO_DIR, "config", "config_test.go")
        assert os.path.isfile(fpath), "config_test.go not found"

    # ------------------------------------------------------------------
    # L2: YAML structure validation
    # ------------------------------------------------------------------

    def test_config_is_valid_yaml(self):
        """Configuration file must be valid YAML."""
        import yaml

        fpath = os.path.join(
            self.REPO_DIR, "documentation", "examples", "multi-job-prometheus.yml"
        )
        with open(fpath, "r") as f:
            config = yaml.safe_load(f)
        assert isinstance(config, dict), "Config root must be a mapping"

    def test_has_scrape_configs(self):
        """Configuration must have scrape_configs section."""
        import yaml

        fpath = os.path.join(
            self.REPO_DIR, "documentation", "examples", "multi-job-prometheus.yml"
        )
        with open(fpath, "r") as f:
            config = yaml.safe_load(f)
        assert "scrape_configs" in config, "scrape_configs not found"

    def test_at_least_3_jobs(self):
        """Must define at least 3 scrape jobs."""
        import yaml

        fpath = os.path.join(
            self.REPO_DIR, "documentation", "examples", "multi-job-prometheus.yml"
        )
        with open(fpath, "r") as f:
            config = yaml.safe_load(f)
        jobs = config.get("scrape_configs", [])
        assert len(jobs) >= 3, f"Need >= 3 jobs, got {len(jobs)}"

    def test_each_job_has_job_name(self):
        """Every job must have a job_name field."""
        import yaml

        fpath = os.path.join(
            self.REPO_DIR, "documentation", "examples", "multi-job-prometheus.yml"
        )
        with open(fpath, "r") as f:
            config = yaml.safe_load(f)
        for job in config.get("scrape_configs", []):
            assert "job_name" in job, f"Job missing job_name: {job}"

    def test_prometheus_self_monitoring_job(self):
        """Must include a 'prometheus' self-monitoring job."""
        import yaml

        fpath = os.path.join(
            self.REPO_DIR, "documentation", "examples", "multi-job-prometheus.yml"
        )
        with open(fpath, "r") as f:
            config = yaml.safe_load(f)
        job_names = [j.get("job_name") for j in config.get("scrape_configs", [])]
        assert (
            "prometheus" in job_names
        ), f"'prometheus' job not found; jobs: {job_names}"

    def test_node_exporter_job_exists(self):
        """Must include a 'node-exporter' job with static_configs."""
        import yaml

        fpath = os.path.join(
            self.REPO_DIR, "documentation", "examples", "multi-job-prometheus.yml"
        )
        with open(fpath, "r") as f:
            config = yaml.safe_load(f)
        for job in config.get("scrape_configs", []):
            if "node" in job.get("job_name", "").lower():
                assert "static_configs" in job, "node-exporter job needs static_configs"
                return
        pytest.fail("node-exporter job not found")

    def test_relabel_configs_present(self):
        """At least one job must have relabel_configs."""
        import yaml

        fpath = os.path.join(
            self.REPO_DIR, "documentation", "examples", "multi-job-prometheus.yml"
        )
        with open(fpath, "r") as f:
            config = yaml.safe_load(f)
        has_relabel = any(
            "relabel_configs" in job for job in config.get("scrape_configs", [])
        )
        assert has_relabel, "No relabel_configs found in any job"

    def test_metric_relabel_configs_present(self):
        """At least one job must have metric_relabel_configs."""
        import yaml

        fpath = os.path.join(
            self.REPO_DIR, "documentation", "examples", "multi-job-prometheus.yml"
        )
        with open(fpath, "r") as f:
            config = yaml.safe_load(f)
        has_metric_relabel = any(
            "metric_relabel_configs" in job for job in config.get("scrape_configs", [])
        )
        assert has_metric_relabel, "No metric_relabel_configs found in any job"

    def test_go_config_tests_pass(self):
        """go test ./config/... must pass."""
        result = subprocess.run(
            ["go", "test", "./config/...", "-v", "-count=1"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=600,
        )
        assert (
            result.returncode == 0
        ), f"Go config tests failed:\n{result.stdout[-2000:]}\n{result.stderr[-1000:]}"

    def test_relabel_has_source_and_target(self):
        """Relabel configs must use source_labels and target_label."""
        import yaml

        fpath = os.path.join(
            self.REPO_DIR, "documentation", "examples", "multi-job-prometheus.yml"
        )
        with open(fpath, "r") as f:
            config = yaml.safe_load(f)
        for job in config.get("scrape_configs", []):
            for rule in job.get("relabel_configs", []):
                if "source_labels" in rule:
                    assert (
                        "target_label" in rule or "action" in rule
                    ), f"relabel rule missing target_label or action: {rule}"
                    return
        pytest.fail("No relabel rule with source_labels found")
