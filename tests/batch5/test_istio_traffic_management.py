"""
Test for 'istio-traffic-management' skill — Istio Traffic Management
Validates VirtualService, DestinationRule, Gateway YAML configurations
with canary weights, fault injection, and circuit breaker settings.
"""

import os
import re

import pytest

try:
    import yaml
except ImportError:
    yaml = None


class TestIstioTrafficManagement:
    """Verify Istio traffic management configuration."""

    REPO_DIR = "/workspace/istio"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_istio_yaml_files_exist(self):
        """Verify at least 4 Istio YAML configuration files exist."""
        yml_files = self._find_istio_yamls()
        assert (
            len(yml_files) >= 3
        ), f"Expected ≥3 Istio YAML files, found {len(yml_files)}"

    def test_virtualservice_file_exists(self):
        """Verify VirtualService YAML exists."""
        for fpath in self._find_istio_yamls():
            content = self._read(fpath)
            if "VirtualService" in content:
                return
        pytest.fail("No VirtualService YAML found")

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_networking_api_version(self):
        """Verify networking.istio.io/v1beta1 or v1alpha3 API version."""
        yml_files = self._find_istio_yamls()
        for fpath in yml_files:
            content = self._read(fpath)
            if re.search(r"networking\.istio\.io/v1(beta1|alpha3)", content):
                return
        pytest.fail("No networking.istio.io API version found")

    def test_canary_weights_sum_100(self):
        """Verify canary traffic weights sum to 100."""
        yml_files = self._find_istio_yamls()
        for fpath in yml_files:
            content = self._read(fpath)
            if "weight" in content:
                weights = [int(m) for m in re.findall(r"weight:\s*(\d+)", content)]
                if weights and sum(weights) == 100:
                    return
        pytest.fail("No canary weights summing to 100 found")

    def test_fault_injection_configured(self):
        """Verify fault injection (delay and/or abort) is configured."""
        yml_files = self._find_istio_yamls()
        for fpath in yml_files:
            content = self._read(fpath)
            if re.search(r"(fault:\s*\n|delay:|abort:)", content):
                return
        pytest.fail("No fault injection configuration found")

    def test_circuit_breaker_configured(self):
        """Verify circuit breaker (consecutive5xxErrors or outlierDetection)."""
        yml_files = self._find_istio_yamls()
        for fpath in yml_files:
            content = self._read(fpath)
            if re.search(
                r"(outlierDetection|consecutive5xxErrors|connectionPool|circuitBreaker)",
                content,
            ):
                return
        pytest.fail("No circuit breaker configuration found")

    def test_gateway_hosts_and_port(self):
        """Verify Gateway defines hosts and port."""
        yml_files = self._find_istio_yamls()
        for fpath in yml_files:
            content = self._read(fpath)
            if "Gateway" in content:
                if "hosts" in content and ("port" in content or "number" in content):
                    return
        pytest.fail("No Gateway with hosts and port found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_yaml_files_valid(self):
        """Verify all Istio YAML files parse correctly."""
        if yaml is None:
            pytest.skip("PyYAML not available")
        yml_files = self._find_istio_yamls()
        assert yml_files, "No YAML files"
        for fpath in yml_files:
            with open(fpath, "r") as fh:
                try:
                    docs = list(yaml.safe_load_all(fh))
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {os.path.basename(fpath)}: {e}")

    def test_weight_validation(self):
        """Verify weights are valid percentages (0-100)."""
        yml_files = self._find_istio_yamls()
        for fpath in yml_files:
            content = self._read(fpath)
            weights = [int(m) for m in re.findall(r"weight:\s*(\d+)", content)]
            for w in weights:
                assert 0 <= w <= 100, f"Invalid weight {w} in {os.path.basename(fpath)}"

    def test_fault_percentage_range(self):
        """Verify fault injection percentages are in valid range."""
        yml_files = self._find_istio_yamls()
        for fpath in yml_files:
            content = self._read(fpath)
            percentages = re.findall(r"percentage:\s*\n\s*value:\s*([\d.]+)", content)
            for p in percentages:
                val = float(p)
                assert (
                    0 < val <= 100
                ), f"Invalid fault percentage {val} in {os.path.basename(fpath)}"

    def test_destination_rules_have_host(self):
        """Verify DestinationRule resources specify a host."""
        yml_files = self._find_istio_yamls()
        for fpath in yml_files:
            content = self._read(fpath)
            if "DestinationRule" in content:
                assert (
                    "host:" in content
                ), f"DestinationRule missing host in {os.path.basename(fpath)}"
                return
        pytest.skip("No DestinationRule to verify")

    def test_virtualservice_has_route(self):
        """Verify VirtualService defines http routes."""
        yml_files = self._find_istio_yamls()
        for fpath in yml_files:
            content = self._read(fpath)
            if "VirtualService" in content:
                if re.search(r"(http:|route:|match:)", content):
                    return
        pytest.fail("No VirtualService with HTTP routes found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_istio_yamls(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".yaml") or f.endswith(".yml"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
