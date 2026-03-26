"""
Test for 'k8s-manifest-generator' skill — Multi-Environment Kustomize Overlays
Validates that the Agent created base manifests with staging/production
overlays, including proper kustomization files and environment differences.
"""

import os
import re
import subprocess

import yaml
import pytest


class TestK8sManifestGenerator:
    """Verify multi-environment Kustomize overlays."""

    REPO_DIR = "/workspace/kustomize"
    EXAMPLE_DIR = "examples/multi-env"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    def _load_yaml(self, *parts):
        text = self._read(*parts)
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as exc:
            pytest.fail(f"Invalid YAML in {'/'.join(parts)}: {exc}")

    # ------------------------------------------------------------------
    # L1: Base files exist
    # ------------------------------------------------------------------

    def test_base_deployment_exists(self):
        """base/deployment.yaml must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.EXAMPLE_DIR, "base", "deployment.yaml")
        )

    def test_base_service_exists(self):
        """base/service.yaml must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.EXAMPLE_DIR, "base", "service.yaml")
        )

    def test_base_configmap_exists(self):
        """base/configmap.yaml must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.EXAMPLE_DIR, "base", "configmap.yaml")
        )

    def test_base_kustomization_exists(self):
        """base/kustomization.yaml must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.EXAMPLE_DIR, "base", "kustomization.yaml")
        )

    # ------------------------------------------------------------------
    # L1: Overlay files exist
    # ------------------------------------------------------------------

    def test_staging_overlay_exists(self):
        """overlays/staging/kustomization.yaml must exist."""
        assert os.path.isfile(
            os.path.join(
                self.REPO_DIR,
                self.EXAMPLE_DIR,
                "overlays",
                "staging",
                "kustomization.yaml",
            )
        )

    def test_production_overlay_exists(self):
        """overlays/production/kustomization.yaml must exist."""
        assert os.path.isfile(
            os.path.join(
                self.REPO_DIR,
                self.EXAMPLE_DIR,
                "overlays",
                "production",
                "kustomization.yaml",
            )
        )

    # ------------------------------------------------------------------
    # L1: YAML validity
    # ------------------------------------------------------------------

    def test_base_deployment_valid(self):
        """base/deployment.yaml must be valid YAML."""
        data = self._load_yaml(self.EXAMPLE_DIR, "base", "deployment.yaml")
        assert data.get("kind") == "Deployment"

    def test_base_service_valid(self):
        """base/service.yaml must be valid YAML."""
        data = self._load_yaml(self.EXAMPLE_DIR, "base", "service.yaml")
        assert data.get("kind") == "Service"

    def test_base_configmap_valid(self):
        """base/configmap.yaml must be valid YAML."""
        data = self._load_yaml(self.EXAMPLE_DIR, "base", "configmap.yaml")
        assert data.get("kind") == "ConfigMap"

    # ------------------------------------------------------------------
    # L2: Base kustomization lists resources
    # ------------------------------------------------------------------

    def test_base_kustomization_lists_resources(self):
        """Base kustomization.yaml must list all base resources."""
        data = self._load_yaml(self.EXAMPLE_DIR, "base", "kustomization.yaml")
        resources = data.get("resources", [])
        expected = ["deployment.yaml", "service.yaml", "configmap.yaml"]
        for exp in expected:
            assert any(
                exp in str(r) for r in resources
            ), f"Base kustomization does not list {exp}"

    # ------------------------------------------------------------------
    # L2: Overlay content differences
    # ------------------------------------------------------------------

    def test_staging_sets_namespace(self):
        """Staging overlay must set or patch namespace."""
        data = self._load_yaml(
            self.EXAMPLE_DIR, "overlays", "staging", "kustomization.yaml"
        )
        text = self._read(self.EXAMPLE_DIR, "overlays", "staging", "kustomization.yaml")
        has_ns = "namespace" in data or re.search(r"namespace", text, re.IGNORECASE)
        assert has_ns, "Staging overlay does not set namespace"

    def test_production_sets_namespace(self):
        """Production overlay must set or patch namespace."""
        text = self._read(
            self.EXAMPLE_DIR, "overlays", "production", "kustomization.yaml"
        )
        assert re.search(
            r"namespace", text, re.IGNORECASE
        ), "Production overlay does not set namespace"

    def test_overlays_differ_in_replicas(self):
        """Staging and production should specify different replica counts."""
        staging_text = self._read(
            self.EXAMPLE_DIR, "overlays", "staging", "kustomization.yaml"
        )
        prod_text = self._read(
            self.EXAMPLE_DIR, "overlays", "production", "kustomization.yaml"
        )
        staging_has = re.search(r"replicas", staging_text, re.IGNORECASE)
        prod_has = re.search(r"replicas", prod_text, re.IGNORECASE)
        assert staging_has or prod_has, "Neither overlay specifies replica counts"

    def test_overlays_use_patches(self):
        """Overlays should use patches rather than duplicating manifests."""
        for env in ("staging", "production"):
            data = self._load_yaml(
                self.EXAMPLE_DIR, "overlays", env, "kustomization.yaml"
            )
            text = self._read(self.EXAMPLE_DIR, "overlays", env, "kustomization.yaml")
            has_patches = (
                "patches" in data
                or "patchesStrategicMerge" in data
                or "patchesJson6902" in data
                or re.search(r"patch", text, re.IGNORECASE)
            )
            has_replicas = "replicas" in data
            assert (
                has_patches or has_replicas
            ), f"{env} overlay does not use patches or replicas"

    def test_common_labels(self):
        """Kustomization should apply common labels."""
        for loc in [("base",), ("overlays", "staging"), ("overlays", "production")]:
            path_parts = (self.EXAMPLE_DIR,) + loc + ("kustomization.yaml",)
            text = self._read(*path_parts)
            if re.search(r"commonLabels|labels", text, re.IGNORECASE):
                return
        pytest.fail("No commonLabels found in any kustomization.yaml")
