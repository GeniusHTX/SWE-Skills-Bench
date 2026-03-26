"""
Test for 'istio-traffic-management' skill — Canary Deployment Example
Validates that the Agent created an Istio canary deployment demo with
VirtualService, DestinationRule, Deployments, and Service manifests.
"""

import os
import re

import yaml
import pytest


class TestIstioTrafficManagement:
    """Verify Istio canary deployment example under samples/canary-demo/."""

    REPO_DIR = "/workspace/istio"
    DEMO_DIR = "samples/canary-demo"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    def _find_yamls(self):
        """Find all YAML files in the canary demo directory."""
        demo = os.path.join(self.REPO_DIR, self.DEMO_DIR)
        assert os.path.isdir(demo), f"Demo directory not found: {demo}"
        results = []
        for root, _dirs, files in os.walk(demo):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    results.append(os.path.join(root, f))
        return results

    def _load_all_docs(self):
        """Load all YAML documents from all files in demo dir."""
        docs = []
        for path in self._find_yamls():
            with open(path, "r", errors="ignore") as fh:
                for doc in yaml.safe_load_all(fh):
                    if doc:
                        docs.append(doc)
        return docs

    # ------------------------------------------------------------------
    # L1: Directory and file existence
    # ------------------------------------------------------------------

    def test_demo_directory_exists(self):
        """samples/canary-demo/ must exist."""
        assert os.path.isdir(os.path.join(self.REPO_DIR, self.DEMO_DIR))

    def test_yaml_files_present(self):
        """At least 2 YAML files must exist in canary-demo/."""
        yamls = self._find_yamls()
        assert len(yamls) >= 2, f"Only {len(yamls)} YAML file(s) in canary-demo/"

    def test_all_yaml_valid(self):
        """Every YAML file in canary-demo must be parseable."""
        for path in self._find_yamls():
            with open(path, "r", errors="ignore") as fh:
                try:
                    list(yaml.safe_load_all(fh))
                except yaml.YAMLError as exc:
                    pytest.fail(f"Invalid YAML in {path}: {exc}")

    # ------------------------------------------------------------------
    # L1: Required Kubernetes/Istio resource kinds
    # ------------------------------------------------------------------

    def test_virtualservice_exists(self):
        """A VirtualService resource must be defined."""
        docs = self._load_all_docs()
        assert any(
            d.get("kind") == "VirtualService" for d in docs
        ), "No VirtualService resource found"

    def test_destinationrule_exists(self):
        """A DestinationRule resource must be defined."""
        docs = self._load_all_docs()
        assert any(
            d.get("kind") == "DestinationRule" for d in docs
        ), "No DestinationRule resource found"

    def test_deployment_exists(self):
        """At least one Deployment resource must be defined."""
        docs = self._load_all_docs()
        deploys = [d for d in docs if d.get("kind") == "Deployment"]
        assert len(deploys) >= 1, "No Deployment resource found"

    def test_service_exists(self):
        """A Service resource must be defined."""
        docs = self._load_all_docs()
        assert any(
            d.get("kind") == "Service" for d in docs
        ), "No Service resource found"

    # ------------------------------------------------------------------
    # L2: VirtualService weighted routing
    # ------------------------------------------------------------------

    def test_virtualservice_has_weights(self):
        """VirtualService must define weighted route destinations."""
        docs = self._load_all_docs()
        vs = next(d for d in docs if d.get("kind") == "VirtualService")
        http_routes = vs.get("spec", {}).get("http", [])
        assert http_routes, "VirtualService has no http routes"
        route = http_routes[0].get("route", [])
        has_weight = any("weight" in dest for dest in route)
        assert has_weight, "VirtualService route has no weight configuration"

    def test_virtualservice_weights_sum_100(self):
        """Route weights should sum to 100."""
        docs = self._load_all_docs()
        vs = next(d for d in docs if d.get("kind") == "VirtualService")
        http_routes = vs.get("spec", {}).get("http", [])
        for hr in http_routes:
            route = hr.get("route", [])
            total = sum(dest.get("weight", 0) for dest in route)
            if total > 0:
                assert total == 100, f"Weights sum to {total}, expected 100"
                return
        pytest.fail("No weighted routes found")

    # ------------------------------------------------------------------
    # L2: DestinationRule subsets
    # ------------------------------------------------------------------

    def test_destinationrule_has_subsets(self):
        """DestinationRule must define at least 2 subsets."""
        docs = self._load_all_docs()
        dr = next(d for d in docs if d.get("kind") == "DestinationRule")
        subsets = dr.get("spec", {}).get("subsets", [])
        assert (
            len(subsets) >= 2
        ), f"DestinationRule has {len(subsets)} subset(s) — need at least 2"

    def test_subsets_have_version_labels(self):
        """Each subset must have version label selectors."""
        docs = self._load_all_docs()
        dr = next(d for d in docs if d.get("kind") == "DestinationRule")
        subsets = dr.get("spec", {}).get("subsets", [])
        for sub in subsets:
            labels = sub.get("labels", {})
            assert (
                "version" in labels
            ), f"Subset '{sub.get('name')}' missing version label"

    # ------------------------------------------------------------------
    # L2: Two deployment versions
    # ------------------------------------------------------------------

    def test_two_deployment_versions(self):
        """Two Deployments with different version labels must exist."""
        docs = self._load_all_docs()
        deploys = [d for d in docs if d.get("kind") == "Deployment"]
        assert (
            len(deploys) >= 2
        ), f"Only {len(deploys)} Deployment(s) — need at least 2 for canary"
        versions = set()
        for dep in deploys:
            labels = (
                dep.get("spec", {})
                .get("template", {})
                .get("metadata", {})
                .get("labels", {})
            )
            v = labels.get("version", "")
            if v:
                versions.add(v)
        assert (
            len(versions) >= 2
        ), f"Only {len(versions)} distinct version label(s): {versions}"
