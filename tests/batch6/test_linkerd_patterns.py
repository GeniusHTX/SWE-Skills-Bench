"""
Tests for 'linkerd-patterns' skill — Linkerd Service Mesh Patterns.
Validates that the Agent generated correct Linkerd ServiceProfile, TrafficSplit,
Server, and AuthorizationPolicy manifests with proper routes, weights,
timeout formats, retry policies, and mTLS authentication references.
"""

import glob
import os
import re
import subprocess
import textwrap

import pytest
import yaml


class TestLinkerdPatterns:
    """Verify Linkerd service mesh configuration manifests."""

    REPO_DIR = "/workspace/linkerd2"
    LINKERD_DIR = os.path.join(REPO_DIR, "linkerd")

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return None

    @staticmethod
    def _load_yaml(path: str):
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return yaml.safe_load(fh)

    def _run_in_repo(
        self, script: str, timeout: int = 120
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python", "-c", textwrap.dedent(script)],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def _yaml_files_in(self, subdir: str):
        pattern = os.path.join(self.LINKERD_DIR, subdir, "*.yaml")
        return glob.glob(pattern)

    # ── file_path_check (static) ────────────────────────────────────────

    def test_service_profiles_dir_exists(self):
        """Verify linkerd/service-profiles/ directory exists with at least 2 YAML files."""
        sp_dir = os.path.join(self.LINKERD_DIR, "service-profiles")
        assert os.path.isdir(sp_dir), f"Missing directory: {sp_dir}"
        yamls = glob.glob(os.path.join(sp_dir, "*.yaml"))
        assert len(yamls) >= 2, f"Expected >= 2 YAML files, found {len(yamls)}"

    def test_traffic_split_exists(self):
        """Verify traffic-split.yaml exists."""
        path = os.path.join(self.LINKERD_DIR, "traffic-split.yaml")
        assert os.path.isfile(path), f"Missing {path}"

    def test_auth_policy_and_server_exist(self):
        """Verify authorization-policy.yaml and server.yaml exist."""
        for fname in ("authorization-policy.yaml", "server.yaml"):
            path = os.path.join(self.LINKERD_DIR, fname)
            assert os.path.isfile(path), f"Missing {path}"

    # ── semantic_check (static) ─────────────────────────────────────────

    def test_service_profile_kind(self):
        """Verify ServiceProfile files have kind: ServiceProfile and apiVersion with linkerd.io."""
        sp_dir = os.path.join(self.LINKERD_DIR, "service-profiles")
        yamls = glob.glob(os.path.join(sp_dir, "*.yaml"))
        assert len(yamls) > 0, "No ServiceProfile YAML files found"
        for fpath in yamls:
            doc = self._load_yaml(fpath)
            assert (
                doc.get("kind") == "ServiceProfile"
            ), f"{fpath}: kind != ServiceProfile"
            assert "linkerd.io" in doc.get(
                "apiVersion", ""
            ), f"{fpath}: apiVersion does not contain linkerd.io"

    def test_traffic_split_has_backends(self):
        """Verify TrafficSplit has spec.backends[] with weight fields."""
        path = os.path.join(self.LINKERD_DIR, "traffic-split.yaml")
        doc = self._load_yaml(path)
        backends = doc.get("spec", {}).get("backends", [])
        assert len(backends) >= 2, f"Expected >= 2 backends, got {len(backends)}"
        for b in backends:
            assert "weight" in b, f"Backend missing weight field: {b}"

    def test_service_profile_routes_defined(self):
        """Verify at least one ServiceProfile has spec.routes with condition."""
        sp_dir = os.path.join(self.LINKERD_DIR, "service-profiles")
        yamls = glob.glob(os.path.join(sp_dir, "*.yaml"))
        found_routes = False
        for fpath in yamls:
            doc = self._load_yaml(fpath)
            routes = doc.get("spec", {}).get("routes", [])
            if routes:
                found_routes = True
                for r in routes:
                    cond = r.get("condition", {})
                    assert cond, f"{fpath}: route missing condition block"
        assert found_routes, "No ServiceProfile has spec.routes defined"

    # ── functional_check (command) ──────────────────────────────────────

    def test_all_linkerd_yaml_parse(self):
        """Verify all Linkerd YAML files parse without error."""
        result = self._run_in_repo(
            """\
            import yaml, glob
            files = glob.glob('linkerd/**/*.yaml', recursive=True)
            assert len(files) >= 4, f'Only {len(files)} files found'
            for f in files:
                yaml.safe_load(open(f))
            print('PASS')
        """
        )
        assert result.returncode == 0, f"Parse failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_traffic_split_weights_sum_100(self):
        """Verify TrafficSplit backend weights sum to 100 or 1.0."""
        result = self._run_in_repo(
            """\
            import yaml
            ts = yaml.safe_load(open('linkerd/traffic-split.yaml'))
            weights = sum(b['weight'] for b in ts['spec']['backends'])
            assert weights == 100 or abs(weights - 1.0) < 0.01, f'Weights sum to {weights}'
            print('PASS')
        """
        )
        assert result.returncode == 0, f"Weight check failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_service_profile_route_count(self):
        """Verify first ServiceProfile has at least 2 routes."""
        result = self._run_in_repo(
            """\
            import yaml, glob
            sps = glob.glob('linkerd/service-profiles/*.yaml')
            sp = yaml.safe_load(open(sps[0]))
            routes = sp['spec']['routes']
            assert len(routes) >= 2, f'Only {len(routes)} routes'
            print('PASS')
        """
        )
        assert result.returncode == 0, f"Route count check failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_timeout_format_valid(self):
        """Verify timeout values have a valid Go duration format (e.g. 10s, 500ms)."""
        result = self._run_in_repo(
            """\
            import yaml, glob, re
            sps = glob.glob('linkerd/service-profiles/*.yaml')
            for f in sps:
                sp = yaml.safe_load(open(f))
                for r in sp['spec']['routes']:
                    t = r.get('timeout', '')
                    if t:
                        assert re.match(r'^\\d+(ms|s|m|h)$', str(t)), f'Invalid timeout: {t}'
            print('PASS')
        """
        )
        assert result.returncode == 0, f"Timeout format check failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_retry_only_idempotent(self):
        """Verify isRetryable is only set on idempotent HTTP methods (GET/HEAD/OPTIONS)."""
        result = self._run_in_repo(
            """\
            import yaml, glob
            sps = glob.glob('linkerd/service-profiles/*.yaml')
            for f in sps:
                sp = yaml.safe_load(open(f))
                for r in sp['spec']['routes']:
                    if r.get('isRetryable'):
                        method = r.get('condition', {}).get('method', '')
                        assert method in ('GET', 'HEAD', 'OPTIONS', ''), (
                            f'Retry on non-idempotent: {method}'
                        )
            print('PASS')
        """
        )
        assert result.returncode == 0, f"Retry idempotent check failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_auth_policy_references_tls(self):
        """Verify AuthorizationPolicy references MeshTLSAuthentication."""
        result = self._run_in_repo(
            """\
            import yaml
            ap = yaml.safe_load(open('linkerd/authorization-policy.yaml'))
            refs = str(ap.get('spec', {}))
            assert 'MeshTLSAuthentication' in refs or 'requiredAuthenticationRefs' in refs, (
                'AuthorizationPolicy does not reference MeshTLSAuthentication'
            )
            print('PASS')
        """
        )
        assert result.returncode == 0, f"TLS ref check failed: {result.stderr}"
        assert "PASS" in result.stdout
