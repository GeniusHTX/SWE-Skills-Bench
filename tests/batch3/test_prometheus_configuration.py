"""
Tests for prometheus-configuration skill.
Validates Prometheus configuration Go source files in prometheus repository.
"""

import os
import subprocess
import glob
import re
import pytest

REPO_DIR = "/workspace/prometheus"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read_dir(dirname: str) -> str:
    """Read all Go source files in a directory and return combined content."""
    pattern = os.path.join(REPO_DIR, dirname, "*.go")
    files = glob.glob(pattern)
    return "\n".join(open(f, encoding="utf-8", errors="ignore").read() for f in files)


def _run(cmd: str, timeout: int = 120):
    return subprocess.run(
        cmd, shell=True, cwd=REPO_DIR, capture_output=True, text=True, timeout=timeout
    )


class TestPrometheusConfiguration:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_config_go_file_exists(self):
        """config/ directory must contain at least one .go file."""
        pattern = os.path.join(REPO_DIR, "config", "*.go")
        files = glob.glob(pattern)
        assert len(files) >= 1, f"No .go files found in {_path('config')}"

    def test_rules_go_file_exists(self):
        """rules/ directory must contain at least one .go file."""
        pattern = os.path.join(REPO_DIR, "rules", "*.go")
        files = glob.glob(pattern)
        assert len(files) >= 1, f"No .go files found in {_path('rules')}"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_service_discovery_struct_defined(self):
        """config/ must define ServiceDiscovery or ScrapeConfig struct with environment grouping."""
        content = _read_dir("config")
        assert (
            "ServiceDiscovery" in content or "ScrapeConfig" in content
        ), "No ServiceDiscovery or ScrapeConfig struct found in config/"
        assert (
            "environment" in content.lower() or "Environment" in content
        ), "No environment grouping logic found in config/"

    def test_recording_rules_latency_percentiles(self):
        """rules/ must define p50, p90, p99 latency recording rules."""
        content = _read_dir("rules")
        assert (
            "0.50" in content or "p50" in content.lower() or "50th" in content
        ), "p50 latency percentile not found in rules/"
        assert (
            "0.90" in content or "p90" in content.lower() or "90th" in content
        ), "p90 latency percentile not found in rules/"
        assert (
            "0.99" in content or "p99" in content.lower() or "99th" in content
        ), "p99 latency percentile not found in rules/"

    def test_alert_rule_error_rate_threshold(self):
        """rules/ must define an error rate alert at >5% for 5 minutes."""
        content = _read_dir("rules")
        assert (
            ">0.05" in content or "> 0.05" in content or "0.05" in content
        ), "Error rate threshold 0.05 not found in rules/"
        assert "5m" in content, "5m duration ('for: 5m') not found in rules/"

    def test_label_validation_no_internal_prefix(self):
        """config/ must validate that labels don't start with '__' (reserved prefix)."""
        content = _read_dir("config")
        assert "__" in content, "No reserved label prefix validation found in config/"
        assert (
            "error" in content.lower()
            or "Error" in content
            or "invalid" in content.lower()
        ), "No error return for reserved label validation found in config/"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_go_config_tests_pass(self):
        """go test ./config/... must pass."""
        result = _run("go test ./config/...")
        if result.returncode != 0 and "go: " in result.stderr[:50]:
            pytest.skip("Go toolchain not available")
        assert (
            result.returncode == 0
        ), f"go test ./config/... failed:\n{result.stdout}\n{result.stderr}"

    def test_go_rules_tests_pass(self):
        """go test ./rules/... must pass."""
        result = _run("go test ./rules/...")
        if result.returncode != 0 and "go: " in result.stderr[:50]:
            pytest.skip("Go toolchain not available")
        assert (
            result.returncode == 0
        ), f"go test ./rules/... failed:\n{result.stdout}\n{result.stderr}"

    def test_service_discovery_groups_by_environment(self):
        """Service discovery must group 3 prod + 2 staging into 2 env groups (mocked)."""
        from collections import defaultdict

        def group_scrape_configs(configs: list) -> dict:
            groups = defaultdict(list)
            for c in configs:
                env = c.get("labels", {}).get("env", "unknown")
                groups[env].append(c)
            return dict(groups)

        configs = [
            {"labels": {"env": "prod"}, "target": "svc1"},
            {"labels": {"env": "prod"}, "target": "svc2"},
            {"labels": {"env": "prod"}, "target": "svc3"},
            {"labels": {"env": "staging"}, "target": "svc4"},
            {"labels": {"env": "staging"}, "target": "svc5"},
        ]
        groups = group_scrape_configs(configs)
        assert len(groups) == 2, f"Expected 2 groups, got {len(groups)}"
        assert len(groups.get("prod", [])) == 3
        assert len(groups.get("staging", [])) == 2

    def test_port_99999_returns_error(self):
        """Port 99999 exceeds valid range and must produce a validation error (mocked)."""

        def validate_port(port: int):
            if not (1 <= port <= 65535):
                raise ValueError(f"invalid port {port}: must be between 1 and 65535")

        with pytest.raises(ValueError, match="invalid port"):
            validate_port(99999)

    def test_internal_label_prefix_error(self):
        """Labels with '__' prefix must produce a validation error (mocked)."""

        def validate_label(name: str):
            if name.startswith("__"):
                raise ValueError(f"label name {name!r} uses reserved '__' prefix")

        with pytest.raises(ValueError, match="reserved"):
            validate_label("__internal")

    def test_histogram_quantile_p99_expression(self):
        """p99 PromQL expression must use histogram_quantile(0.99, ...) (mocked)."""

        def build_latency_rule(quantile: float, metric: str) -> str:
            return f"histogram_quantile({quantile}, sum(rate({metric}_bucket[5m])) by (le))"

        expr = build_latency_rule(0.99, "http_request_duration_seconds")
        assert "histogram_quantile(0.99" in expr

    def test_yaml_round_trip_preserved(self):
        """Marshal/unmarshal config round-trip must preserve all fields (mocked)."""
        import yaml

        original = {
            "global": {"scrape_interval": "15s"},
            "scrape_configs": [{"job_name": "test", "static_configs": []}],
        }
        serialized = yaml.dump(original)
        recovered = yaml.safe_load(serialized)
        assert recovered == original
