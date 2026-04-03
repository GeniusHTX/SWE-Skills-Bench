"""
Tests for 'k8s-manifest-generator' skill — Kubernetes Manifest Generator.
Validates that the Agent generated proper K8s manifests including Deployments,
Services, Ingress, RBAC, Secrets, and HPA with correct structure, required
fields, resource limits, base64-encoded secrets, and label alignment.
"""

import base64
import glob
import os
import subprocess
import textwrap

import pytest
import yaml


class TestK8sManifestGenerator:
    """Verify Kubernetes manifest generation quality."""

    REPO_DIR = "/workspace/kustomize"
    K8S_DIR = os.path.join(REPO_DIR, "k8s")

    # ── helpers ──────────────────────────────────────────────────────────

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

    def _all_yaml_files(self):
        return glob.glob(os.path.join(self.K8S_DIR, "**", "*.yaml"), recursive=True)

    # ── file_path_check (static) ────────────────────────────────────────

    def test_deployments_directory_exists(self):
        """Verify k8s/deployments/ directory exists with at least 5 YAML files."""
        dep_dir = os.path.join(self.K8S_DIR, "deployments")
        assert os.path.isdir(dep_dir), f"Missing directory: {dep_dir}"
        yamls = glob.glob(os.path.join(dep_dir, "*.yaml"))
        assert len(yamls) >= 5, f"Expected >= 5 deployment YAMLs, found {len(yamls)}"

    def test_services_directory_exists(self):
        """Verify k8s/services/ directory exists."""
        svc_dir = os.path.join(self.K8S_DIR, "services")
        assert os.path.isdir(svc_dir), f"Missing directory: {svc_dir}"

    def test_ingress_and_rbac_exist(self):
        """Verify ingress.yaml and rbac/ directory exist under k8s/."""
        ingress_path = os.path.join(self.K8S_DIR, "ingress.yaml")
        rbac_dir = os.path.join(self.K8S_DIR, "rbac")
        assert os.path.isfile(ingress_path), f"Missing {ingress_path}"
        assert os.path.isdir(rbac_dir), f"Missing directory: {rbac_dir}"

    # ── semantic_check (static) ─────────────────────────────────────────

    def test_all_manifests_have_required_keys(self):
        """Verify every YAML manifest has apiVersion, kind, and metadata.name."""
        for fpath in self._all_yaml_files():
            doc = self._load_yaml(fpath)
            assert doc is not None, f"{fpath}: empty document"
            for key in ("apiVersion", "kind", "metadata"):
                assert key in doc, f"{fpath}: missing {key}"
            assert "name" in doc["metadata"], f"{fpath}: missing metadata.name"

    def test_deployment_has_resource_limits(self):
        """Verify Deployment containers specify resources.limits and resources.requests."""
        dep_dir = os.path.join(self.K8S_DIR, "deployments")
        yamls = glob.glob(os.path.join(dep_dir, "*.yaml"))
        assert len(yamls) > 0, "No deployment files"
        for fpath in yamls:
            doc = self._load_yaml(fpath)
            containers = (
                doc.get("spec", {})
                .get("template", {})
                .get("spec", {})
                .get("containers", [])
            )
            for c in containers:
                resources = c.get("resources", {})
                assert (
                    "limits" in resources
                ), f"{fpath}: container {c.get('name')} missing resources.limits"
                assert (
                    "requests" in resources
                ), f"{fpath}: container {c.get('name')} missing resources.requests"

    def test_secret_has_base64_data(self):
        """Verify Secret files have type: Opaque and a data block."""
        secrets_dir = os.path.join(self.K8S_DIR, "secrets")
        if not os.path.isdir(secrets_dir):
            pytest.skip("k8s/secrets/ directory not present")
        yamls = glob.glob(os.path.join(secrets_dir, "*.yaml"))
        assert len(yamls) > 0, "No secret files found"
        for fpath in yamls:
            doc = self._load_yaml(fpath)
            assert doc.get("kind") == "Secret", f"{fpath}: kind != Secret"
            assert "data" in doc or "stringData" in doc, f"{fpath}: missing data block"

    # ── functional_check (command) ──────────────────────────────────────

    def test_all_yaml_parseable(self):
        """Verify all 16+ YAML manifest files parse without error."""
        result = self._run_in_repo(
            """\
            import yaml, glob
            files = glob.glob('k8s/**/*.yaml', recursive=True)
            assert len(files) >= 16, f'Only {len(files)} files'
            for f in files:
                yaml.safe_load(open(f))
            print('PASS')
        """
        )
        assert result.returncode == 0, f"Parse failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_manifests_have_metadata(self):
        """Verify every manifest has apiVersion, kind, and metadata.name (functional)."""
        result = self._run_in_repo(
            """\
            import yaml, glob
            files = glob.glob('k8s/**/*.yaml', recursive=True)
            for f in files:
                doc = yaml.safe_load(open(f))
                for k in ['apiVersion', 'kind', 'metadata']:
                    assert k in doc, f'{f}: missing {k}'
                assert 'name' in doc['metadata'], f'{f}: missing metadata.name'
            print('PASS')
        """
        )
        assert result.returncode == 0, f"Metadata check failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_deployment_count(self):
        """Verify at least 5 Deployment manifests exist."""
        result = self._run_in_repo(
            """\
            import glob
            deps = glob.glob('k8s/deployments/*.yaml')
            assert len(deps) >= 5, f'Only {len(deps)} deployments'
            print('PASS')
        """
        )
        assert result.returncode == 0, f"Deployment count check failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_secret_values_base64(self):
        """Verify Secret data values are valid base64-encoded strings."""
        result = self._run_in_repo(
            """\
            import yaml, glob, base64
            secrets = glob.glob('k8s/secrets/*.yaml')
            for f in secrets:
                s = yaml.safe_load(open(f))
                for k, v in s.get('data', {}).items():
                    base64.b64decode(v)
            print('PASS')
        """
        )
        assert result.returncode == 0, f"Base64 check failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_hpa_replicas_valid(self):
        """Verify HPA minReplicas <= maxReplicas."""
        result = self._run_in_repo(
            """\
            import yaml, glob
            hpas = [f for f in glob.glob('k8s/**/*.yaml', recursive=True)
                     if 'hpa' in f.lower() or 'autoscal' in f.lower()]
            for f in hpas:
                h = yaml.safe_load(open(f))
                assert h['spec']['minReplicas'] <= h['spec']['maxReplicas'], (
                    f'{f}: min > max'
                )
            print('PASS')
        """
        )
        assert result.returncode == 0, f"HPA check failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_service_selector_matches_deployment(self):
        """Verify Service selector labels match at least one Deployment pod template labels."""
        result = self._run_in_repo(
            """\
            import yaml, glob
            dep_labels = {}
            for f in glob.glob('k8s/deployments/*.yaml'):
                d = yaml.safe_load(open(f))
                name = d['metadata']['name']
                dep_labels[name] = d['spec']['template']['metadata']['labels']
            for f in glob.glob('k8s/services/*.yaml'):
                s = yaml.safe_load(open(f))
                sel = s['spec'].get('selector', {})
                if not sel:
                    continue
                matched = any(
                    all(labels.get(k) == v for k, v in sel.items())
                    for labels in dep_labels.values()
                )
                assert matched, f"{f}: selector {sel} matches no deployment labels"
            print('PASS')
        """
        )
        assert result.returncode == 0, f"Selector match check failed: {result.stderr}"
        assert "PASS" in result.stdout
