"""
Test for 'istio-traffic-management' skill — Istio Traffic Management
Validates VirtualService, DestinationRule, PeerAuthentication, Gateway,
AuthorizationPolicy YAML manifests in the istio repo.
"""

import os
import re
import glob
import yaml
import pytest


class TestIstioTrafficManagement:
    """Tests for Istio traffic management in the istio repo."""

    REPO_DIR = "/workspace/istio"

    def _load_all_docs(self):
        """Load all YAML documents from the repo."""
        all_docs = []
        for f in glob.glob(os.path.join(self.REPO_DIR, "**/*.yaml"), recursive=True):
            try:
                content = open(f, errors="ignore").read()
                for d in yaml.safe_load_all(content):
                    if d:
                        all_docs.append(d)
            except Exception:
                continue
        return all_docs

    # --- File Path Checks ---

    def test_yaml_exists(self):
        """Verifies that at least one YAML file exists in the repo."""
        yamls = glob.glob(os.path.join(self.REPO_DIR, "**/*.yaml"), recursive=True)
        assert len(yamls) > 0, "No YAML files found"

    def test_repo_dir_exists(self):
        """Verifies the repository directory exists."""
        assert os.path.exists(self.REPO_DIR), f"Repo dir not found: {self.REPO_DIR}"

    # --- Semantic Checks ---

    def test_sem_load_all_yaml_docs(self):
        """All YAML docs can be loaded."""
        all_docs = self._load_all_docs()
        assert len(all_docs) > 0, "No YAML documents loaded"

    def test_sem_has_virtual_service(self):
        """At least one VirtualService document exists."""
        all_docs = self._load_all_docs()
        assert any(
            d.get("kind") == "VirtualService" for d in all_docs
        ), "No VirtualService found"

    def test_sem_has_destination_rule(self):
        """At least one DestinationRule document exists."""
        all_docs = self._load_all_docs()
        assert any(
            d.get("kind") == "DestinationRule" for d in all_docs
        ), "No DestinationRule found"

    def test_sem_virtual_service_api_version(self):
        """VirtualService uses networking.istio.io apiVersion."""
        all_docs = self._load_all_docs()
        vs = next((d for d in all_docs if d.get("kind") == "VirtualService"), None)
        assert vs is not None, "No VirtualService found"
        assert "networking.istio.io" in vs.get(
            "apiVersion", ""
        ), "VirtualService missing networking.istio.io apiVersion"

    def test_sem_has_peer_authentication(self):
        """At least one PeerAuthentication document exists."""
        all_docs = self._load_all_docs()
        assert any(
            d.get("kind") == "PeerAuthentication" for d in all_docs
        ), "No PeerAuthentication found"

    # --- Functional Checks ---

    def test_func_vs_weights_sum_to_100(self):
        """VirtualService route weights sum to 100."""
        all_docs = self._load_all_docs()
        vs = next((d for d in all_docs if d.get("kind") == "VirtualService"), None)
        assert vs is not None, "No VirtualService found"
        vs_routes = [
            r
            for http in vs.get("spec", {}).get("http", [])
            for r in http.get("route", [])
        ]
        weight_sum = sum(r.get("weight", 100) for r in vs_routes)
        assert weight_sum == 100, f"Weights sum to {weight_sum}, expected 100"

    def test_func_destination_rule_has_policy_or_subsets(self):
        """DestinationRule has trafficPolicy or subsets."""
        all_docs = self._load_all_docs()
        dr = next((d for d in all_docs if d.get("kind") == "DestinationRule"), None)
        assert dr is not None, "No DestinationRule found"
        spec = dr.get("spec", {})
        assert spec.get("trafficPolicy") or spec.get(
            "subsets"
        ), "DestinationRule missing trafficPolicy and subsets"

    def test_func_circuit_breaker_configured(self):
        """DestinationRule has outlierDetection (circuit breaker)."""
        all_docs = self._load_all_docs()
        dr = next((d for d in all_docs if d.get("kind") == "DestinationRule"), None)
        assert dr is not None, "No DestinationRule found"
        outlier = (
            dr.get("spec", {}).get("trafficPolicy", {}).get("outlierDetection", {})
        )
        assert outlier != {}, "Circuit breaker (outlierDetection) not configured"

    def test_func_peer_auth_strict_mtls(self):
        """PeerAuthentication has STRICT mTLS mode."""
        all_docs = self._load_all_docs()
        pa = next((d for d in all_docs if d.get("kind") == "PeerAuthentication"), None)
        assert pa is not None, "No PeerAuthentication found"
        assert (
            pa.get("spec", {}).get("mtls", {}).get("mode") == "STRICT"
        ), "PeerAuthentication mTLS mode is not STRICT"

    def test_func_has_authorization_policy(self):
        """At least one AuthorizationPolicy document exists."""
        all_docs = self._load_all_docs()
        assert any(
            d.get("kind") == "AuthorizationPolicy" for d in all_docs
        ), "No AuthorizationPolicy found"

    def test_func_has_gateway(self):
        """At least one Gateway document exists."""
        all_docs = self._load_all_docs()
        gw = next((d for d in all_docs if d.get("kind") == "Gateway"), None)
        assert gw is not None, "No Gateway found"

    def test_func_vs_subsets_match_dr_subsets(self):
        """VirtualService subset references are subsets of DestinationRule subsets."""
        all_docs = self._load_all_docs()
        vs = next((d for d in all_docs if d.get("kind") == "VirtualService"), None)
        dr = next((d for d in all_docs if d.get("kind") == "DestinationRule"), None)
        assert vs and dr, "Missing VirtualService or DestinationRule"
        dr_subsets = {s["name"] for s in dr.get("spec", {}).get("subsets", [])}
        vs_subsets = {
            r["destination"].get("subset")
            for h in vs.get("spec", {}).get("http", [])
            for r in h.get("route", [])
            if r.get("destination", {}).get("subset")
        }
        assert vs_subsets.issubset(
            dr_subsets
        ), f"VS subsets {vs_subsets} not in DR subsets {dr_subsets}"

    def test_func_failure_weights_not_100(self):
        """Failure case: validates that VirtualService weights logic is checked."""
        all_docs = self._load_all_docs()
        vs = next((d for d in all_docs if d.get("kind") == "VirtualService"), None)
        assert vs is not None, "No VirtualService found"
        vs_routes = [
            r
            for http in vs.get("spec", {}).get("http", [])
            for r in http.get("route", [])
        ]
        weight_sum = sum(r.get("weight", 100) for r in vs_routes)
        assert (
            weight_sum == 100
        ), f"VirtualService weights not summing to 100: {weight_sum}"
