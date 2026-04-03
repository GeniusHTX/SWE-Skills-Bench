"""
Test for 'istio-traffic-management' skill — Istio Traffic Management
Validates VirtualServiceBuilder, DestinationRuleBuilder, GatewayBuilder,
PeerAuthBuilder with weight validation, mTLS, and YAML generation.
"""

import os
import sys

import pytest


class TestIstioTrafficManagement:
    """Verify Istio traffic management builders and YAML generation."""

    REPO_DIR = "/workspace/istio"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _ist(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "examples", "istio", *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_init_py_exists(self):
        """examples/istio/__init__.py must exist."""
        assert os.path.isfile(self._ist("__init__.py")), "__init__.py not found"

    def test_virtual_service_py_exists(self):
        """virtual_service.py must exist."""
        assert os.path.isfile(self._ist("virtual_service.py")), "virtual_service.py not found"

    def test_destination_rule_gateway_peer_auth_exist(self):
        """destination_rule.py, gateway.py, peer_auth.py must exist."""
        for name in ("destination_rule.py", "gateway.py", "peer_auth.py"):
            assert os.path.isfile(self._ist(name)), f"{name} not found"

    def test_test_file_exists(self):
        """tests/test_istio.py must exist."""
        path = os.path.join(self.REPO_DIR, "tests", "test_istio.py")
        assert os.path.isfile(path), f"{path} not found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_weight_sum_validation(self):
        """VirtualServiceBuilder must validate sum(weights) == 100."""
        content = self._read_file(self._ist("virtual_service.py"))
        if not content:
            pytest.skip("virtual_service.py not found")
        assert "sum" in content or "100" in content
        assert "ValueError" in content

    def test_apiversion_v1beta1_not_v1alpha3(self):
        """Builders must use networking.istio.io/v1beta1, not v1alpha3."""
        for name in ("virtual_service.py", "destination_rule.py"):
            content = self._read_file(self._ist(name))
            if content:
                assert "v1beta1" in content, f"v1beta1 not found in {name}"
                assert "v1alpha3" not in content, f"Deprecated v1alpha3 in {name}"

    def test_destination_rule_mtls(self):
        """DestinationRule must reference ISTIO_MUTUAL mode."""
        content = self._read_file(self._ist("destination_rule.py"))
        if not content:
            pytest.skip("destination_rule.py not found")
        assert "ISTIO_MUTUAL" in content

    def test_peer_auth_strict_mode(self):
        """PeerAuthentication must use STRICT mode."""
        content = self._read_file(self._ist("peer_auth.py"))
        if not content:
            pytest.skip("peer_auth.py not found")
        assert "STRICT" in content

    # ── functional_check ─────────────────────────────────────────────────

    def test_80_20_split_yaml(self):
        """VirtualService 80/20 split must produce valid YAML with sum 100."""
        try:
            import yaml
            sys.path.insert(0, self.REPO_DIR)
            from examples.istio.virtual_service import VirtualServiceBuilder
        except ImportError:
            pytest.skip("Cannot import VirtualServiceBuilder or yaml")
        vs = VirtualServiceBuilder(hosts=["myapp"], weights=[80, 20])
        config = yaml.safe_load(vs.build())
        assert config["apiVersion"] == "networking.istio.io/v1beta1"
        routes = config["spec"]["http"][0]["route"]
        assert sum(r["weight"] for r in routes) == 100

    def test_invalid_weights_raise_valueerror(self):
        """Weights summing to 110 must raise ValueError."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.istio.virtual_service import VirtualServiceBuilder
        except ImportError:
            pytest.skip("Cannot import VirtualServiceBuilder")
        with pytest.raises(ValueError):
            VirtualServiceBuilder(hosts=["myapp"], weights=[50, 60]).build()

    def test_destination_rule_mtls_yaml(self):
        """DestinationRule with mtls=True must produce ISTIO_MUTUAL in YAML."""
        try:
            import yaml
            sys.path.insert(0, self.REPO_DIR)
            from examples.istio.destination_rule import DestinationRuleBuilder
        except ImportError:
            pytest.skip("Cannot import DestinationRuleBuilder")
        dr = DestinationRuleBuilder(host="myapp", mtls=True)
        config = yaml.safe_load(dr.build())
        assert config["spec"]["trafficPolicy"]["tls"]["mode"] == "ISTIO_MUTUAL"

    def test_single_host_100_percent(self):
        """Single backend at 100% weight must be valid."""
        try:
            import yaml
            sys.path.insert(0, self.REPO_DIR)
            from examples.istio.virtual_service import VirtualServiceBuilder
        except ImportError:
            pytest.skip("Cannot import VirtualServiceBuilder")
        vs = VirtualServiceBuilder(hosts=["myapp"], weights=[100])
        config = yaml.safe_load(vs.build())
        routes = config["spec"]["http"][0]["route"]
        assert len(routes) == 1 and routes[0]["weight"] == 100

    def test_all_builders_produce_valid_yaml(self):
        """All builders must produce YAML with apiVersion and kind."""
        try:
            import yaml
            sys.path.insert(0, self.REPO_DIR)
            from examples.istio.virtual_service import VirtualServiceBuilder
            from examples.istio.destination_rule import DestinationRuleBuilder
            from examples.istio.gateway import GatewayBuilder
        except ImportError:
            pytest.skip("Cannot import builders")
        builders = [
            VirtualServiceBuilder(hosts=["myapp"], weights=[100]),
            DestinationRuleBuilder(host="myapp"),
            GatewayBuilder(hosts=["myapp"]),
        ]
        for b in builders:
            config = yaml.safe_load(b.build())
            assert "apiVersion" in config
            assert "kind" in config
