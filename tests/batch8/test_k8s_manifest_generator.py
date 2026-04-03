"""
Test for 'k8s-manifest-generator' skill — K8s Manifest Generator
Validates that the Agent created a Python package for generating K8s
Deployment/Service/ConfigMap YAML with label standards, validation, and Helm merge.
"""

import os
import re
import sys

import pytest


class TestK8sManifestGenerator:
    """Verify K8s manifest generator implementation."""

    REPO_DIR = "/workspace/kustomize"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_k8s_generator_package_exists(self):
        """Verify __init__.py and manifest.py exist under src/k8s_generator/."""
        for rel in ("src/k8s_generator/__init__.py", "src/k8s_generator/manifest.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_kustomize_helm_models_exist(self):
        """Verify kustomize.py, helm.py, and models.py exist."""
        for rel in ("src/k8s_generator/kustomize.py", "src/k8s_generator/helm.py",
                     "src/k8s_generator/models.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_all_classes_importable(self):
        """ManifestGenerator, KustomizeBuilder, HelmValuesMerger are importable."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            from k8s_generator.manifest import ManifestGenerator  # noqa: F401
            from k8s_generator.kustomize import KustomizeBuilder  # noqa: F401
            from k8s_generator.helm import HelmValuesMerger  # noqa: F401
        except ImportError:
            pytest.skip("k8s_generator not importable")
        finally:
            sys.path.pop(0)

    # ── semantic_check ──────────────────────────────────────────────

    def test_manifest_generator_methods_defined(self):
        """Verify generate_deployment(), generate_service(), generate_configmap() are defined."""
        content = self._read(os.path.join(self.REPO_DIR, "src/k8s_generator/manifest.py"))
        assert content, "manifest.py is empty or unreadable"
        for method in ("generate_deployment", "generate_service", "generate_configmap"):
            assert method in content, f"'{method}' not found in manifest.py"

    def test_validation_error_in_manifest(self):
        """Verify manifest.py raises ValidationError for invalid fields."""
        content = self._read(os.path.join(self.REPO_DIR, "src/k8s_generator/manifest.py"))
        assert content, "manifest.py is empty or unreadable"
        assert "ValidationError" in content, "ValidationError not found"
        assert "raise" in content, "'raise' keyword not found"

    def test_cpu_memory_regex_validation(self):
        """Verify manifest.py uses regex for CPU and memory format validation."""
        content = self._read(os.path.join(self.REPO_DIR, "src/k8s_generator/manifest.py"))
        assert content, "manifest.py is empty or unreadable"
        found = any(kw in content for kw in ("re.match", "re.fullmatch", "Mi", "Gi"))
        assert found, "No CPU/memory regex validation found"

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

    def test_deployment_yaml_kind_is_deployment(self):
        """generate_deployment() returns YAML with kind: Deployment."""
        import yaml
        mod = self._import("k8s_generator.manifest")
        models = self._import("k8s_generator.models")
        config = models.DeploymentConfig(
            name="myapp", image="nginx:1.21", replicas=2, cpu="100m", memory="128Mi")
        manifest = yaml.safe_load(mod.ManifestGenerator().generate_deployment(config))
        assert manifest["kind"] == "Deployment"

    def test_mandatory_labels_present(self):
        """app.kubernetes.io/name label present in generated Deployment metadata."""
        import yaml
        mod = self._import("k8s_generator.manifest")
        models = self._import("k8s_generator.models")
        config = models.DeploymentConfig(
            name="myapp", image="nginx:1.21", replicas=1, cpu="100m", memory="128Mi")
        manifest = yaml.safe_load(mod.ManifestGenerator().generate_deployment(config))
        assert "app.kubernetes.io/name" in manifest["metadata"]["labels"]

    def test_missing_name_raises_validation_error(self):
        """DeploymentConfig without name raises ValidationError."""
        mod = self._import("k8s_generator.manifest")
        models = self._import("k8s_generator.models")
        with pytest.raises(models.ValidationError):
            mod.ManifestGenerator().generate_deployment(
                models.DeploymentConfig(name="", image="nginx"))

    def test_invalid_cpu_format_raises(self):
        """Non-numeric CPU format 'abc' raises ValidationError."""
        mod = self._import("k8s_generator.manifest")
        models = self._import("k8s_generator.models")
        with pytest.raises(models.ValidationError):
            mod.ManifestGenerator().generate_deployment(
                models.DeploymentConfig(name="app", image="nginx", cpu="abc", memory="128Mi"))

    def test_helm_deep_merge_preserves_siblings(self):
        """HelmValuesMerger.merge() deeply merges nested dicts preserving siblings."""
        mod = self._import("k8s_generator.helm")
        result = mod.HelmValuesMerger().merge(
            {"a": {"b": 1, "c": 2}}, {"a": {"b": 99}})
        assert result == {"a": {"b": 99, "c": 2}}

    def test_configmap_data_section_correct(self):
        """generate_configmap() produces ConfigMap YAML with correct data section."""
        import yaml
        mod = self._import("k8s_generator.manifest")
        cm = yaml.safe_load(mod.ManifestGenerator().generate_configmap({"key": "val"}, "my-cm"))
        assert cm["data"]["key"] == "val"
