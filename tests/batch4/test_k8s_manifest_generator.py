"""
Test for 'k8s-manifest-generator' skill — K8s Manifest Generator
Validates ManifestGenerator class that produces Deployment, Service, ConfigMap,
Ingress manifests and multi-document YAML output.
"""

import os
import re
import sys
import pytest

import yaml


class TestK8sManifestGenerator:
    """Tests for K8s manifest generation in the kustomize repo."""

    REPO_DIR = "/workspace/kustomize"

    def _read(self, relpath):
        full = os.path.join(self.REPO_DIR, relpath)
        with open(full, "r", errors="ignore") as f:
            return f.read()

    # --- File Path Checks ---

    def test_generator_py_exists(self):
        """Verifies that examples/manifest_gen/generator.py exists."""
        path = os.path.join(self.REPO_DIR, "examples", "manifest_gen", "generator.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_init_py_exists(self):
        """Verifies that examples/manifest_gen/__init__.py exists."""
        path = os.path.join(self.REPO_DIR, "examples", "manifest_gen", "__init__.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    # --- Semantic Checks ---

    def test_sem_import_manifest_generator(self):
        """from examples.manifest_gen.generator import ManifestGenerator — importable."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from examples.manifest_gen.generator import ManifestGenerator

            assert ManifestGenerator is not None
        finally:
            sys.path[:] = old_path

    def test_sem_manifest_generator_methods(self):
        """ManifestGenerator has generate_deployment, generate_service, generate_configmap, generate_ingress, generate_all, to_yaml."""
        content = self._read("examples/manifest_gen/generator.py")
        for method in [
            "generate_deployment",
            "generate_service",
            "generate_configmap",
            "generate_ingress",
            "generate_all",
            "to_yaml",
        ]:
            assert re.search(
                rf"def\s+{method}\s*\(", content
            ), f"Method {method} not found"

    def test_sem_constructor_validates_required(self):
        """Constructor raises on missing required fields."""
        content = self._read("examples/manifest_gen/generator.py")
        assert (
            "raise" in content.lower() or "ValueError" in content
        ), "No validation/raise found for missing required fields"

    # --- Functional Checks (import) ---

    def test_func_create_generator(self):
        """ManifestGenerator(spec) creates successfully with valid spec."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from examples.manifest_gen.generator import ManifestGenerator

            spec = {
                "name": "myapp",
                "image": "nginx:1.21",
                "replicas": 2,
                "port": 8080,
                "namespace": "default",
            }
            gen = ManifestGenerator(spec)
            assert gen is not None
        finally:
            sys.path[:] = old_path

    def test_func_deployment_kind_and_api_version(self):
        """generate_deployment returns dict with kind='Deployment' and apiVersion='apps/v1'."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from examples.manifest_gen.generator import ManifestGenerator

            spec = {
                "name": "myapp",
                "image": "nginx:1.21",
                "replicas": 2,
                "port": 8080,
                "namespace": "default",
            }
            gen = ManifestGenerator(spec)
            dep = gen.generate_deployment()
            assert dep["kind"] == "Deployment"
            assert dep["apiVersion"] == "apps/v1"
        finally:
            sys.path[:] = old_path

    def test_func_deployment_metadata_name(self):
        """dep['metadata']['name'] == 'myapp'."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from examples.manifest_gen.generator import ManifestGenerator

            spec = {
                "name": "myapp",
                "image": "nginx:1.21",
                "replicas": 2,
                "port": 8080,
                "namespace": "default",
            }
            gen = ManifestGenerator(spec)
            dep = gen.generate_deployment()
            assert dep["metadata"]["name"] == "myapp"
        finally:
            sys.path[:] = old_path

    def test_func_deployment_replicas(self):
        """dep['spec']['replicas'] == 2."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from examples.manifest_gen.generator import ManifestGenerator

            spec = {
                "name": "myapp",
                "image": "nginx:1.21",
                "replicas": 2,
                "port": 8080,
                "namespace": "default",
            }
            gen = ManifestGenerator(spec)
            dep = gen.generate_deployment()
            assert dep["spec"]["replicas"] == 2
        finally:
            sys.path[:] = old_path

    def test_func_deployment_container_image(self):
        """Container image matches spec image 'nginx:1.21'."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from examples.manifest_gen.generator import ManifestGenerator

            spec = {
                "name": "myapp",
                "image": "nginx:1.21",
                "replicas": 2,
                "port": 8080,
                "namespace": "default",
            }
            gen = ManifestGenerator(spec)
            dep = gen.generate_deployment()
            assert (
                dep["spec"]["template"]["spec"]["containers"][0]["image"]
                == "nginx:1.21"
            )
        finally:
            sys.path[:] = old_path

    def test_func_service_kind_and_selector(self):
        """generate_service returns Service with selector matching deployment."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from examples.manifest_gen.generator import ManifestGenerator

            spec = {
                "name": "myapp",
                "image": "nginx:1.21",
                "replicas": 2,
                "port": 8080,
                "namespace": "default",
            }
            gen = ManifestGenerator(spec)
            dep = gen.generate_deployment()
            svc = gen.generate_service()
            assert svc["kind"] == "Service"
            assert svc["spec"]["selector"] == dep["spec"]["selector"]["matchLabels"]
        finally:
            sys.path[:] = old_path

    def test_func_configmap(self):
        """generate_configmap produces ConfigMap with correct data."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from examples.manifest_gen.generator import ManifestGenerator

            spec = {
                "name": "myapp",
                "image": "nginx:1.21",
                "replicas": 2,
                "port": 8080,
                "namespace": "default",
            }
            gen = ManifestGenerator(spec)
            cm = gen.generate_configmap({"KEY": "value"})
            assert cm["kind"] == "ConfigMap"
            assert cm["data"]["KEY"] == "value"
        finally:
            sys.path[:] = old_path

    def test_func_to_yaml_multi_doc(self):
        """to_yaml produces valid multi-document YAML with >= 2 docs."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from examples.manifest_gen.generator import ManifestGenerator

            spec = {
                "name": "myapp",
                "image": "nginx:1.21",
                "replicas": 2,
                "port": 8080,
                "namespace": "default",
            }
            gen = ManifestGenerator(spec)
            yaml_str = gen.to_yaml()
            docs = list(yaml.safe_load_all(yaml_str))
            assert len(docs) >= 2, f"Expected >= 2 docs, got {len(docs)}"
        finally:
            sys.path[:] = old_path

    def test_func_edge_namespace_defaults(self):
        """Namespace not in spec defaults to 'default'."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from examples.manifest_gen.generator import ManifestGenerator

            spec = {"name": "myapp", "image": "nginx:1.21", "replicas": 1, "port": 80}
            gen = ManifestGenerator(spec)
            dep = gen.generate_deployment()
            ns = dep.get("metadata", {}).get("namespace", "default")
            assert ns == "default", f"Expected 'default' namespace, got '{ns}'"
        finally:
            sys.path[:] = old_path

    def test_func_failure_empty_spec(self):
        """spec={} raises ValueError for missing name."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from examples.manifest_gen.generator import ManifestGenerator

            with pytest.raises((ValueError, KeyError, TypeError)):
                ManifestGenerator({})
        finally:
            sys.path[:] = old_path
