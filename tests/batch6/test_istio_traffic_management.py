"""
Tests for 'istio-traffic-management' skill — Istio Traffic Management.
Validates that the Agent generated correct Istio VirtualService, DestinationRule,
and PeerAuthentication manifests with proper weights, subsets, mTLS, and
header-based canary routing.
"""

import glob
import os
import re
import subprocess
import textwrap

import pytest
import yaml


class TestIstioTrafficManagement:
    """Verify Istio traffic management manifests."""

    REPO_DIR = "/workspace/istio"
    ISTIO_DIR = os.path.join(REPO_DIR, "istio")

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        """Read a file and return its content, or None on failure."""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return None

    @staticmethod
    def _load_yaml(path: str):
        """Parse a YAML file and return the top-level object."""
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return yaml.safe_load(fh)

    def _run_in_repo(
        self, script: str, timeout: int = 120
    ) -> subprocess.CompletedProcess:
        """Run a Python inline script inside REPO_DIR."""
        return subprocess.run(
            ["python", "-c", textwrap.dedent(script)],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    # ── file_path_check (static) ────────────────────────────────────────

    def test_virtual_service_exists(self):
        """Verify VirtualService YAML exists at istio/virtual-service.yaml."""
        path = os.path.join(self.ISTIO_DIR, "virtual-service.yaml")
        assert os.path.isfile(path), f"Missing {path}"

    def test_destination_rule_exists(self):
        """Verify DestinationRule YAML exists at istio/destination-rule.yaml."""
        path = os.path.join(self.ISTIO_DIR, "destination-rule.yaml")
        assert os.path.isfile(path), f"Missing {path}"

    def test_peer_authentication_exists(self):
        """Verify PeerAuthentication YAML exists at istio/peer-authentication.yaml."""
        path = os.path.join(self.ISTIO_DIR, "peer-authentication.yaml")
        assert os.path.isfile(path), f"Missing {path}"

    # ── semantic_check (static) ─────────────────────────────────────────

    def test_vs_has_http_routes(self):
        """Verify VirtualService has kind: VirtualService and http routes with weight fields."""
        path = os.path.join(self.ISTIO_DIR, "virtual-service.yaml")
        doc = self._load_yaml(path)
        assert doc.get("kind") == "VirtualService", "kind is not VirtualService"
        http_routes = doc.get("spec", {}).get("http", [])
        assert len(http_routes) > 0, "No http routes defined in VirtualService"
        has_weight = any(
            "weight" in dest for route in http_routes for dest in route.get("route", [])
        )
        assert has_weight, "No weight field found in any http route destination"

    def test_dr_has_subsets(self):
        """Verify DestinationRule defines v1 and v2 subsets."""
        path = os.path.join(self.ISTIO_DIR, "destination-rule.yaml")
        doc = self._load_yaml(path)
        subsets = doc.get("spec", {}).get("subsets", [])
        subset_names = {s.get("name") for s in subsets}
        assert "v1" in subset_names, "Missing subset v1"
        assert "v2" in subset_names, "Missing subset v2"

    def test_pa_mtls_strict(self):
        """Verify PeerAuthentication has mTLS mode STRICT."""
        path = os.path.join(self.ISTIO_DIR, "peer-authentication.yaml")
        doc = self._load_yaml(path)
        mode = doc.get("spec", {}).get("mtls", {}).get("mode")
        assert mode == "STRICT", f"Expected STRICT, got {mode}"

    # ── functional_check (command) ──────────────────────────────────────

    def test_all_istio_yaml_parseable(self):
        """Verify all Istio YAML files parse without error using yaml.safe_load."""
        result = self._run_in_repo(
            """\
            import yaml, glob
            files = glob.glob('istio/*.yaml')
            assert len(files) >= 4, f'Only {len(files)} YAML files found'
            for f in files:
                yaml.safe_load(open(f))
            print('PASS')
        """
        )
        assert result.returncode == 0, f"Parse failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_route_weights_sum_100(self):
        """Verify that default VirtualService route weights sum to 100."""
        result = self._run_in_repo(
            """\
            import yaml
            vs = yaml.safe_load(open('istio/virtual-service.yaml'))
            routes = [r for r in vs['spec']['http'] if 'match' not in r]
            total = sum(d['weight'] for r in routes for d in r['route'])
            assert total == 100, f'Weights sum to {total}'
            print('PASS')
        """
        )
        assert result.returncode == 0, f"Weight check failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_dr_subsets_v1_v2(self):
        """Verify DestinationRule subsets contain v1 and v2 via functional parsing."""
        result = self._run_in_repo(
            """\
            import yaml
            dr = yaml.safe_load(open('istio/destination-rule.yaml'))
            names = [s['name'] for s in dr['spec']['subsets']]
            assert 'v1' in names and 'v2' in names, f'Subsets: {names}'
            print('PASS')
        """
        )
        assert result.returncode == 0, f"Subsets check failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_peer_auth_strict_mode(self):
        """Verify PeerAuthentication mode is exactly STRICT (functional)."""
        result = self._run_in_repo(
            """\
            import yaml
            pa = yaml.safe_load(open('istio/peer-authentication.yaml'))
            mode = pa['spec']['mtls']['mode']
            assert mode == 'STRICT', f'Mode is {mode}'
            print('PASS')
        """
        )
        assert result.returncode == 0, f"Strict mode check failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_canary_header_routing(self):
        """Verify header-based canary routing to v2 exists in VirtualService."""
        result = self._run_in_repo(
            """\
            import yaml
            vs = yaml.safe_load(open('istio/virtual-service.yaml'))
            canary = [r for r in vs['spec']['http'] if 'match' in r]
            assert len(canary) > 0, 'No canary route with match'
            match_str = str(canary[0])
            assert 'v2' in match_str or 'canary' in match_str, (
                f'Canary route does not reference v2 or canary: {match_str[:200]}'
            )
            print('PASS')
        """
        )
        assert result.returncode == 0, f"Canary check failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_api_version_correct(self):
        """Verify VirtualService apiVersion contains networking.istio.io."""
        result = self._run_in_repo(
            """\
            import yaml
            vs = yaml.safe_load(open('istio/virtual-service.yaml'))
            assert 'networking.istio.io' in vs['apiVersion'], (
                f"Wrong apiVersion: {vs['apiVersion']}"
            )
            print('PASS')
        """
        )
        assert result.returncode == 0, f"apiVersion check failed: {result.stderr}"
        assert "PASS" in result.stdout
