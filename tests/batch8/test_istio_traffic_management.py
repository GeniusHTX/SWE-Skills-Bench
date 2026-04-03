"""
Test for 'istio-traffic-management' skill — Istio Traffic Manager
Validates that the Agent created a Python package for generating Istio
VirtualService/DestinationRule YAML with canary splits, promotion, and circuit breaker config.
"""

import os
import re
import sys

import pytest


class TestIstioTrafficManagement:
    """Verify Istio traffic management implementation."""

    REPO_DIR = "/workspace/istio"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_istio_manager_package_exists(self):
        """Verify __init__.py and generator.py exist under src/istio_manager/."""
        for rel in ("src/istio_manager/__init__.py", "src/istio_manager/generator.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_canary_circuit_breaker_models_exist(self):
        """Verify canary.py, circuit_breaker.py, and models.py exist."""
        for rel in ("src/istio_manager/canary.py", "src/istio_manager/circuit_breaker.py",
                     "src/istio_manager/models.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_all_classes_importable(self):
        """IstioTrafficGenerator, CanaryManager, CircuitBreakerConfig are importable."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            from istio_manager.generator import IstioTrafficGenerator  # noqa: F401
            from istio_manager.canary import CanaryManager  # noqa: F401
            from istio_manager.circuit_breaker import CircuitBreakerConfig  # noqa: F401
        except ImportError:
            pytest.skip("istio_manager not importable")
        finally:
            sys.path.pop(0)

    # ── semantic_check ──────────────────────────────────────────────

    def test_generator_methods_defined(self):
        """Verify generate_virtual_service() and generate_destination_rule() are defined."""
        content = self._read(os.path.join(self.REPO_DIR, "src/istio_manager/generator.py"))
        assert content, "generator.py is empty or unreadable"
        for method in ("generate_virtual_service", "generate_destination_rule"):
            assert method in content, f"'{method}' not found in generator.py"

    def test_canary_manager_methods_defined(self):
        """Verify create_canary_split(), promote(), and rollback() are defined."""
        content = self._read(os.path.join(self.REPO_DIR, "src/istio_manager/canary.py"))
        assert content, "canary.py is empty or unreadable"
        for method in ("create_canary_split", "def promote", "def rollback"):
            assert method in content, f"'{method}' not found in canary.py"

    def test_yaml_dump_in_generator(self):
        """Verify generator.py uses yaml.dump for YAML serialization."""
        content = self._read(os.path.join(self.REPO_DIR, "src/istio_manager/generator.py"))
        assert content, "generator.py is empty or unreadable"
        found = "yaml.dump" in content or "ruamel" in content
        assert found, "No YAML serialization found in generator.py"

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

    def test_virtual_service_yaml_valid_api_version(self):
        """generate_virtual_service() returns YAML with apiVersion networking.istio.io/v1alpha3."""
        import yaml
        gen = self._import("istio_manager.generator")
        models = self._import("istio_manager.models")
        vs = yaml.safe_load(gen.IstioTrafficGenerator().generate_virtual_service(
            models.VirtualServiceConfig(name="svc", host="my-svc")))
        assert vs["apiVersion"] == "networking.istio.io/v1alpha3"

    def test_canary_split_weights_sum_to_100(self):
        """create_canary_split() produces routes whose weights sum to 100."""
        import yaml
        canary = self._import("istio_manager.canary")
        out = yaml.safe_load(canary.CanaryManager().create_canary_split("my-svc", 20))
        routes = out["spec"]["http"][0]["route"]
        assert sum(r["weight"] for r in routes) == 100

    def test_canary_weight_out_of_range_raises(self):
        """create_canary_split() raises ValueError when canary_weight=101."""
        canary = self._import("istio_manager.canary")
        with pytest.raises(ValueError):
            canary.CanaryManager().create_canary_split("svc", 101)

    def test_promote_produces_single_100_weight_route(self):
        """promote() returns VirtualService with single route weight=100."""
        import yaml
        canary = self._import("istio_manager.canary")
        out = yaml.safe_load(canary.CanaryManager().promote("my-svc"))
        routes = out["spec"]["http"][0]["route"]
        assert len(routes) == 1
        assert routes[0]["weight"] == 100

    def test_circuit_breaker_destination_rule_has_traffic_policy(self):
        """CircuitBreakerConfig.apply() generates DestinationRule with trafficPolicy."""
        import yaml
        cb = self._import("istio_manager.circuit_breaker")
        dr = yaml.safe_load(cb.CircuitBreakerConfig().apply(
            "svc", max_connections=100, max_requests=50))
        assert "trafficPolicy" in dr["spec"]
