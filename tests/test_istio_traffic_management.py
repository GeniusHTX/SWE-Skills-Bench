"""
Test for 'istio-traffic-management' skill — Istio Traffic Management
Validates that the Agent created VirtualService, DestinationRule, Gateway,
Deployments configs and a verify script for canary routing with proper traffic weights.
"""

import os
import pytest


class TestIstioTrafficManagement:
    """Verify Istio traffic management configs."""

    REPO_DIR = "/workspace/istio"
    CANARY_DIR = "samples/canary-demo"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_virtualservice_exists(self):
        """samples/canary-demo/virtual-service.yaml must exist."""
        fpath = os.path.join(self.REPO_DIR, self.CANARY_DIR, "virtual-service.yaml")
        assert os.path.isfile(fpath), "virtual-service.yaml not found"

    def test_destinationrule_exists(self):
        """samples/canary-demo/destination-rule.yaml must exist."""
        fpath = os.path.join(self.REPO_DIR, self.CANARY_DIR, "destination-rule.yaml")
        assert os.path.isfile(fpath), "destination-rule.yaml not found"

    def test_gateway_exists(self):
        """samples/canary-demo/gateway.yaml must exist."""
        fpath = os.path.join(self.REPO_DIR, self.CANARY_DIR, "gateway.yaml")
        assert os.path.isfile(fpath), "gateway.yaml not found"

    def test_deployments_exists(self):
        """samples/canary-demo/deployments.yaml must exist."""
        fpath = os.path.join(self.REPO_DIR, self.CANARY_DIR, "deployments.yaml")
        assert os.path.isfile(fpath), "deployments.yaml not found"

    def test_verify_sh_exists(self):
        """samples/canary-demo/verify.sh must exist."""
        fpath = os.path.join(self.REPO_DIR, self.CANARY_DIR, "verify.sh")
        assert os.path.isfile(fpath), "verify.sh not found"

    # ------------------------------------------------------------------
    # L2: YAML content validation
    # ------------------------------------------------------------------

    def _load_yamls(self, relpath):
        import yaml

        fpath = os.path.join(self.REPO_DIR, relpath)
        with open(fpath, "r") as f:
            return list(yaml.safe_load_all(f))

    def test_virtualservice_kind(self):
        """VirtualService file must define kind: VirtualService."""
        docs = self._load_yamls(f"{self.CANARY_DIR}/virtual-service.yaml")
        vs_found = any(d and d.get("kind") == "VirtualService" for d in docs)
        assert vs_found, "No VirtualService resource found"

    def test_destinationrule_kind(self):
        """DestinationRule file must define kind: DestinationRule."""
        docs = self._load_yamls(f"{self.CANARY_DIR}/destination-rule.yaml")
        dr_found = any(d and d.get("kind") == "DestinationRule" for d in docs)
        assert dr_found, "No DestinationRule resource found"

    def test_virtualservice_has_http_routes(self):
        """VirtualService must define HTTP routes."""
        docs = self._load_yamls(f"{self.CANARY_DIR}/virtual-service.yaml")
        for doc in docs:
            if doc and doc.get("kind") == "VirtualService":
                spec = doc.get("spec", {})
                http = spec.get("http", [])
                assert len(http) >= 1, "VirtualService has no HTTP routes"
                return
        pytest.fail("No VirtualService with spec.http found")

    def test_traffic_weights_sum_to_100(self):
        """Route weights in a single match must sum to 100."""
        docs = self._load_yamls(f"{self.CANARY_DIR}/virtual-service.yaml")
        for doc in docs:
            if doc and doc.get("kind") == "VirtualService":
                for route_block in doc.get("spec", {}).get("http", []):
                    routes = route_block.get("route", [])
                    if len(routes) >= 2:
                        total = sum(r.get("weight", 0) for r in routes)
                        assert total == 100, f"Weights sum to {total}, expected 100"
                        return
        pytest.fail("No route block with >= 2 weighted destinations found")

    def test_destinationrule_has_subsets(self):
        """DestinationRule must define at least 2 subsets."""
        docs = self._load_yamls(f"{self.CANARY_DIR}/destination-rule.yaml")
        for doc in docs:
            if doc and doc.get("kind") == "DestinationRule":
                subsets = doc.get("spec", {}).get("subsets", [])
                assert len(subsets) >= 2, f"Need >= 2 subsets, got {len(subsets)}"
                return
        pytest.fail("No DestinationRule with subsets found")

    def test_subsets_have_labels(self):
        """Each subset must have version labels."""
        docs = self._load_yamls(f"{self.CANARY_DIR}/destination-rule.yaml")
        for doc in docs:
            if doc and doc.get("kind") == "DestinationRule":
                subsets = doc.get("spec", {}).get("subsets", [])
                for subset in subsets:
                    assert "name" in subset, "Subset missing name"
                    labels = subset.get("labels", {})
                    assert len(labels) >= 1, f"Subset '{subset['name']}' has no labels"
                return

    def test_virtualservice_has_hosts(self):
        """VirtualService must specify hosts."""
        docs = self._load_yamls(f"{self.CANARY_DIR}/virtual-service.yaml")
        for doc in docs:
            if doc and doc.get("kind") == "VirtualService":
                hosts = doc.get("spec", {}).get("hosts", [])
                assert len(hosts) >= 1, "VirtualService has no hosts"
                return

    def test_verify_sh_contains_istioctl(self):
        """verify.sh must call istioctl analyze for validation."""
        fpath = os.path.join(self.REPO_DIR, self.CANARY_DIR, "verify.sh")
        with open(fpath, "r", errors="ignore") as fh:
            content = fh.read()
        assert "istioctl" in content, "verify.sh does not invoke istioctl analyze"

    def test_yaml_files_parseable(self):
        """Core YAML files must contain valid YAML."""
        import yaml

        for fname in [
            "virtual-service.yaml",
            "destination-rule.yaml",
            "gateway.yaml",
            "deployments.yaml",
        ]:
            fpath = os.path.join(self.REPO_DIR, self.CANARY_DIR, fname)
            with open(fpath, "r") as f:
                docs = list(yaml.safe_load_all(f))
            assert all(
                isinstance(d, dict) for d in docs if d is not None
            ), f"{fname} contains non-mapping documents"
