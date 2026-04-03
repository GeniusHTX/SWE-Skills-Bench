"""
Test for 'linkerd-patterns' skill — Linkerd Service Mesh Configuration
Validates ServiceProfile, TrafficSplit YAMLs with retryable routes,
weight sums, timeout bounds, and edge cases.
"""

import os
import re

import pytest

try:
    import yaml
except ImportError:
    yaml = None


class TestLinkerdPatterns:
    """Verify Linkerd service mesh configuration patterns."""

    REPO_DIR = "/workspace/linkerd2"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_service_profile_yaml_exists(self):
        """Verify ServiceProfile YAML file exists."""
        for fpath in self._find_yaml_files():
            content = self._read(fpath)
            if "ServiceProfile" in content:
                return
        pytest.fail("No ServiceProfile YAML found")

    def test_traffic_split_yaml_exists(self):
        """Verify TrafficSplit YAML file exists."""
        for fpath in self._find_yaml_files():
            content = self._read(fpath)
            if "TrafficSplit" in content:
                return
        pytest.fail("No TrafficSplit YAML found")

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_linkerd_api_version(self):
        """Verify linkerd.io/v1alpha2 or similar API version."""
        for fpath in self._find_yaml_files():
            content = self._read(fpath)
            if re.search(r"linkerd\.io/v1alpha[12]", content):
                return
            if re.search(r"split\.smi-spec\.io", content):
                return
        pytest.fail("No Linkerd API version found")

    def test_get_retryable_true(self):
        """Verify GET routes are marked isRetryable: true."""
        for fpath in self._find_yaml_files():
            content = self._read(fpath)
            if "ServiceProfile" in content:
                if "GET" in content and "isRetryable" in content:
                    return
        pytest.fail("No GET route with isRetryable found")

    def test_post_not_retryable(self):
        """Verify POST routes are NOT retryable (or omitted)."""
        for fpath in self._find_yaml_files():
            content = self._read(fpath)
            if "ServiceProfile" in content and "POST" in content:
                # Check that POST is not marked retryable
                lines = content.split("\n")
                in_post = False
                for line in lines:
                    if "POST" in line:
                        in_post = True
                    if in_post and "isRetryable: true" in line:
                        pytest.fail("POST route should not be retryable")
                    if in_post and line.strip().startswith("- "):
                        in_post = False
                return
        pytest.skip("No POST route in ServiceProfile to verify")

    def test_traffic_split_weights_sum_1000m(self):
        """Verify TrafficSplit weights sum to 1000m (or 1)."""
        for fpath in self._find_yaml_files():
            content = self._read(fpath)
            if "TrafficSplit" not in content:
                continue
            weights = re.findall(r"weight:\s*(\d+)m?", content)
            if weights:
                total = sum(int(w) for w in weights)
                # Could be in milliunits (1000m) or units (1 or 100)
                assert total in (
                    1000,
                    100,
                    1,
                ), f"TrafficSplit weights sum to {total}, expected 1000m or 100 or 1"
                return
        pytest.fail("No TrafficSplit weights found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_yaml_files_valid(self):
        """Verify all YAML files parse correctly."""
        if yaml is None:
            pytest.skip("PyYAML not available")
        for fpath in self._find_yaml_files():
            with open(fpath, "r") as fh:
                try:
                    list(yaml.safe_load_all(fh))
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {os.path.basename(fpath)}: {e}")

    def test_retryable_filter_logic(self):
        """Verify routes with isRetryable are GET-only (idempotent)."""
        for fpath in self._find_yaml_files():
            content = self._read(fpath)
            if "ServiceProfile" not in content:
                continue
            if yaml is None:
                pytest.skip("PyYAML not available")
            with open(fpath, "r") as fh:
                for doc in yaml.safe_load_all(fh):
                    if not isinstance(doc, dict):
                        continue
                    spec = doc.get("spec", {})
                    routes = spec.get("routes", [])
                    for route in routes:
                        if not isinstance(route, dict):
                            continue
                        if route.get("isRetryable"):
                            condition = route.get("condition", {})
                            method = condition.get("method", "")
                            assert method in (
                                "GET",
                                "HEAD",
                                "OPTIONS",
                                "",
                            ), f"Non-idempotent method {method} marked retryable"
            return
        pytest.skip("No ServiceProfile to verify")

    def test_weight_sum_validation(self):
        """Verify no negative weights exist."""
        for fpath in self._find_yaml_files():
            content = self._read(fpath)
            weights = re.findall(r"weight:\s*(-?\d+)", content)
            for w in weights:
                assert int(w) >= 0, f"Negative weight {w} found"

    def test_timeout_bounds(self):
        """Verify route timeouts are positive durations."""
        for fpath in self._find_yaml_files():
            content = self._read(fpath)
            if "timeout" in content.lower():
                timeouts = re.findall(r"timeout:\s*(\S+)", content)
                for t in timeouts:
                    assert re.match(r"\d+[smh]?s?$", t), f"Invalid timeout format: {t}"
                return
        pytest.skip("No timeout configuration found")

    def test_service_profile_has_routes(self):
        """Verify ServiceProfile defines at least one route."""
        for fpath in self._find_yaml_files():
            content = self._read(fpath)
            if "ServiceProfile" in content and "routes:" in content:
                return
        pytest.fail("No ServiceProfile with routes found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_yaml_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath or "vendor" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".yaml") or f.endswith(".yml"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
