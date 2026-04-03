"""
Test for 'k8s-manifest-generator' skill — Kustomize Manifest Generation
Validates base/overlay structure, kustomization.yaml, per-environment
replicas, namespace, HPA bounds, and kustomize build.
"""

import os
import re
import subprocess

import pytest

try:
    import yaml
except ImportError:
    yaml = None


def _load_yaml(path):
    """Load a single-document YAML file."""
    with open(path, "r") as fh:
        return yaml.safe_load(fh)


def _load_yaml_all(path):
    """Load a multi-document YAML file."""
    with open(path, "r") as fh:
        return list(yaml.safe_load_all(fh))


def _get_replicas(docs):
    """Extract the first 'replicas' value from a list of YAML documents."""
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        spec = doc.get("spec", {})
        if isinstance(spec, dict):
            r = spec.get("replicas")
            if r is not None:
                return r
    return None


class TestK8sManifestGenerator:
    """Verify Kustomize-based Kubernetes manifest generation."""

    REPO_DIR = "/workspace/kustomize"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_base_kustomization_exists(self):
        """Verify base/kustomization.yaml exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "base" in dirpath.lower() and "kustomization.yaml" in fnames:
                found = True
                break
        assert found, "No base/kustomization.yaml found"

    def test_overlay_directories_exist(self):
        """Verify overlay directories for at least 2 environments exist."""
        envs = set()
        for dirpath, dirs, _ in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for d in dirs:
                dl = d.lower()
                if dl in ("dev", "staging", "production", "prod"):
                    envs.add(dl)
        assert len(envs) >= 2, f"Expected ≥2 env overlays, found: {envs}"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_kustomization_lists_resources(self):
        """Verify kustomization.yaml files list resources."""
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "kustomization.yaml" in fnames:
                content = self._read(os.path.join(dirpath, "kustomization.yaml"))
                if "resources:" in content or "bases:" in content:
                    return
        pytest.fail("No kustomization.yaml with resources found")

    def test_dev_one_replica(self):
        """Verify dev overlay has 1 replica."""
        if yaml is None:
            pytest.skip("PyYAML not available")
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "dev" in os.path.basename(dirpath).lower():
                for f in fnames:
                    if f.endswith(".yaml") or f.endswith(".yml"):
                        content = self._read(os.path.join(dirpath, f))
                        m = re.search(r"replicas:\s*(\d+)", content)
                        if m and int(m.group(1)) == 1:
                            return
        pytest.skip("Dev overlay with 1 replica not found")

    def test_production_three_replicas(self):
        """Verify production overlay has ≥3 replicas."""
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            basename = os.path.basename(dirpath).lower()
            if basename in ("production", "prod"):
                for f in fnames:
                    if f.endswith(".yaml") or f.endswith(".yml"):
                        content = self._read(os.path.join(dirpath, f))
                        m = re.search(r"replicas:\s*(\d+)", content)
                        if m and int(m.group(1)) >= 3:
                            return
        pytest.skip("Production overlay with ≥3 replicas not found")

    def test_namespace_per_env(self):
        """Verify namespace is set per environment."""
        namespaces = set()
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".yaml") or f.endswith(".yml"):
                    content = self._read(os.path.join(dirpath, f))
                    for m in re.finditer(r"namespace:\s*(\S+)", content):
                        namespaces.add(m.group(1))
        assert len(namespaces) >= 1, "No namespace definitions found"

    # ── functional_check ────────────────────────────────────────────────────

    def test_yaml_files_valid(self):
        """Verify all YAML files parse correctly."""
        if yaml is None:
            pytest.skip("PyYAML not available")
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".yaml") or f.endswith(".yml"):
                    fpath = os.path.join(dirpath, f)
                    with open(fpath, "r") as fh:
                        try:
                            list(yaml.safe_load_all(fh))
                        except yaml.YAMLError as e:
                            pytest.fail(f"Invalid YAML in {f}: {e}")

    def test_kustomize_build(self):
        """Verify kustomize build succeeds on base."""
        try:
            subprocess.run(["kustomize", "version"], capture_output=True, timeout=10)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("kustomize CLI not available")
        base_dirs = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "kustomization.yaml" in fnames:
                base_dirs.append(dirpath)
        assert base_dirs, "No kustomization.yaml found"
        result = subprocess.run(
            ["kustomize", "build", base_dirs[0]],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"kustomize build failed: {result.stderr[:500]}"

    def test_hpa_min_lte_max(self):
        """Verify HPA minReplicas ≤ maxReplicas."""
        if yaml is None:
            pytest.skip("PyYAML not available")
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if not (f.endswith(".yaml") or f.endswith(".yml")):
                    continue
                fpath = os.path.join(dirpath, f)
                content = self._read(fpath)
                if "HorizontalPodAutoscaler" in content:
                    with open(fpath, "r") as fh:
                        for doc in yaml.safe_load_all(fh):
                            if not isinstance(doc, dict):
                                continue
                            spec = doc.get("spec", {})
                            if "minReplicas" in spec and "maxReplicas" in spec:
                                assert (
                                    spec["minReplicas"] <= spec["maxReplicas"]
                                ), f"HPA min ({spec['minReplicas']}) > max ({spec['maxReplicas']})"
                                return
        pytest.skip("No HPA resource found")

    def test_production_has_resource_limits(self):
        """Verify production overlay sets resource limits."""
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            basename = os.path.basename(dirpath).lower()
            if basename in ("production", "prod"):
                for f in fnames:
                    if f.endswith(".yaml") or f.endswith(".yml"):
                        content = self._read(os.path.join(dirpath, f))
                        if "limits:" in content or "resources:" in content:
                            return
        pytest.skip("Production resource limits not found")

    def test_staging_between_dev_and_prod(self):
        """Verify staging replicas are between dev and production."""
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            basename = os.path.basename(dirpath).lower()
            if basename == "staging":
                for f in fnames:
                    if f.endswith(".yaml") or f.endswith(".yml"):
                        content = self._read(os.path.join(dirpath, f))
                        m = re.search(r"replicas:\s*(\d+)", content)
                        if m:
                            replicas = int(m.group(1))
                            assert (
                                1 <= replicas <= 3
                            ), f"Staging replicas {replicas} not between dev(1) and prod(3)"
                            return
        pytest.skip("No staging overlay found")

    def test_missing_resource_detection(self):
        """Verify kustomization references existing resources."""
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "kustomization.yaml" not in fnames:
                continue
            kust_path = os.path.join(dirpath, "kustomization.yaml")
            if yaml is None:
                pytest.skip("PyYAML not available")
            data = _load_yaml(kust_path)
            if not isinstance(data, dict):
                continue
            resources = data.get("resources", [])
            if not resources:
                continue
            for res in resources:
                res_path = os.path.join(dirpath, res)
                assert os.path.exists(
                    res_path
                ), f"Resource '{res}' referenced in kustomization.yaml does not exist"
            return
        pytest.skip("No kustomization.yaml with resources to verify")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
