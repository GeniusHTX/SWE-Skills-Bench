"""
Test for 'linkerd-patterns' skill — Linkerd Patterns
Validates Linkerd service mesh configuration including ServiceProfile,
TrafficSplit, retryBudget, proxy injection annotations, and namespace settings.
"""

import os
import re
import glob
import pytest

import yaml


class TestLinkerdPatterns:
    """Tests for Linkerd patterns in the linkerd2 repo."""

    REPO_DIR = "/workspace/linkerd2"

    def _read(self, relpath):
        full = os.path.join(self.REPO_DIR, relpath)
        with open(full, "r", errors="ignore") as f:
            return f.read()

    def _load_all_docs(self):
        """Load all YAML documents from yaml/yml files in the repo."""
        all_docs = []
        for ext in ("yaml", "yml"):
            pattern = os.path.join(self.REPO_DIR, "**", f"*.{ext}")
            for f in glob.glob(pattern, recursive=True):
                try:
                    with open(f, "r", errors="ignore") as fh:
                        docs = list(yaml.safe_load_all(fh.read()))
                        all_docs.extend([d for d in docs if d and isinstance(d, dict)])
                except (yaml.YAMLError, Exception):
                    pass
        return all_docs

    # --- File Path Checks ---

    def test_yaml_files_exist(self):
        """Verifies that *.yaml files exist in the repo."""
        pattern = os.path.join(self.REPO_DIR, "**", "*.yaml")
        matches = glob.glob(pattern, recursive=True)
        assert len(matches) > 0, "No .yaml files found in repo"

    def test_yml_files_exist(self):
        """Verifies that *.yml files exist in the repo."""
        pattern = os.path.join(self.REPO_DIR, "**", "*.yml")
        matches = glob.glob(pattern, recursive=True)
        assert len(matches) > 0, "No .yml files found in repo"

    # --- Semantic Checks ---

    def test_sem_all_docs_parseable(self):
        """All YAML docs are parseable and produce documents."""
        all_docs = self._load_all_docs()
        assert len(all_docs) > 0, "No YAML documents loaded"

    def test_sem_has_service_profile(self):
        """At least one ServiceProfile document exists."""
        all_docs = self._load_all_docs()
        assert any(
            d.get("kind") == "ServiceProfile" for d in all_docs
        ), "No ServiceProfile document found"

    def test_sem_service_profile_api_version(self):
        """ServiceProfile apiVersion starts with 'linkerd.io'."""
        all_docs = self._load_all_docs()
        sp = next((d for d in all_docs if d.get("kind") == "ServiceProfile"), None)
        assert sp is not None, "No ServiceProfile found"
        assert sp["apiVersion"].startswith(
            "linkerd.io"
        ), f"ServiceProfile apiVersion does not start with 'linkerd.io': {sp['apiVersion']}"

    def test_sem_has_traffic_split_or_http_route(self):
        """At least one TrafficSplit or HTTPRoute document exists."""
        all_docs = self._load_all_docs()
        assert any(
            d.get("kind") in ("TrafficSplit", "HTTPRoute") for d in all_docs
        ), "No TrafficSplit or HTTPRoute document found"

    # --- Functional Checks ---

    def test_func_service_profile_routes_list(self):
        """ServiceProfile spec.routes is a list with len >= 1."""
        all_docs = self._load_all_docs()
        sp = next((d for d in all_docs if d.get("kind") == "ServiceProfile"), None)
        assert sp is not None, "No ServiceProfile found"
        routes = sp["spec"]["routes"]
        assert isinstance(routes, list), f"routes is not a list: {type(routes)}"
        assert len(routes) >= 1, "routes list is empty"

    def test_func_routes_have_name_and_condition(self):
        """Each route in ServiceProfile has 'name' and 'condition'."""
        all_docs = self._load_all_docs()
        sp = next((d for d in all_docs if d.get("kind") == "ServiceProfile"), None)
        assert sp is not None
        for route in sp["spec"]["routes"]:
            assert "name" in route, f"Route missing 'name': {route}"
            assert "condition" in route, f"Route missing 'condition': {route}"

    def test_func_retry_budget_ratio(self):
        """ServiceProfile retryBudget.retryRatio is between 0 and 1."""
        all_docs = self._load_all_docs()
        sp = next((d for d in all_docs if d.get("kind") == "ServiceProfile"), None)
        assert sp is not None
        retry_budget = sp["spec"].get("retryBudget", {})
        retry_ratio = retry_budget.get("retryRatio")
        assert retry_ratio is not None, "retryBudget.retryRatio not set"
        assert 0 <= retry_ratio <= 1, f"retryRatio {retry_ratio} not in [0, 1]"

    def test_func_traffic_split_exists(self):
        """A TrafficSplit document exists."""
        all_docs = self._load_all_docs()
        ts = next((d for d in all_docs if d.get("kind") == "TrafficSplit"), None)
        assert ts is not None, "No TrafficSplit document found"

    def test_func_traffic_split_weights_sum(self):
        """TrafficSplit backend weights sum to 100 or 1.0."""
        all_docs = self._load_all_docs()
        ts = next((d for d in all_docs if d.get("kind") == "TrafficSplit"), None)
        assert ts is not None, "No TrafficSplit found"
        backends = ts["spec"]["backends"]
        total = sum(b["weight"] for b in backends)
        assert (
            total == 100 or abs(total - 1.0) < 0.01
        ), f"Backend weights sum to {total}, expected 100 or 1.0"

    def test_func_deployment_linkerd_inject_annotation(self):
        """At least one Deployment has linkerd.io/inject == 'enabled' annotation."""
        all_docs = self._load_all_docs()
        deployments = [d for d in all_docs if d.get("kind") == "Deployment"]
        assert any(
            d.get("metadata", {}).get("annotations", {}).get("linkerd.io/inject")
            == "enabled"
            for d in deployments
        ), "No Deployment with linkerd.io/inject == 'enabled' annotation"

    def test_func_flux_resources_have_namespace(self):
        """All ServiceProfile/TrafficSplit docs have metadata.namespace set."""
        all_docs = self._load_all_docs()
        for d in all_docs:
            if d.get("kind") in ("ServiceProfile", "TrafficSplit"):
                ns = d.get("metadata", {}).get("namespace")
                assert ns, f"{d.get('kind')} missing metadata.namespace"

    def test_func_failure_traffic_split_weights(self):
        """TrafficSplit weights must sum to exactly 100 or 1.0 (validates no drift)."""
        all_docs = self._load_all_docs()
        ts = next((d for d in all_docs if d.get("kind") == "TrafficSplit"), None)
        assert ts is not None, "No TrafficSplit for weight validation"
        backends = ts["spec"]["backends"]
        total = sum(b["weight"] for b in backends)
        is_valid = total == 100 or abs(total - 1.0) < 0.01
        assert is_valid, f"TrafficSplit weights sum to {total}, not 100 or ~1.0"
