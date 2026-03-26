"""
Test for 'gitops-workflow' skill — Flux GitOps Configuration
Validates that the Agent created a complete GitOps configuration example
for Flux with source, kustomizations, base manifests, and overlays.
"""

import os
import re

import yaml
import pytest


class TestGitopsWorkflow:
    """Verify Flux GitOps configuration example."""

    REPO_DIR = "/workspace/flux2"
    DEMO_DIR = "examples/gitops-demo"

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
    # L1: Required files exist
    # ------------------------------------------------------------------

    def test_source_yaml_exists(self):
        """source.yaml must exist in the gitops-demo directory."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, self.DEMO_DIR, "source.yaml"))

    def test_staging_kustomization_exists(self):
        """staging-kustomization.yaml must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.DEMO_DIR, "staging-kustomization.yaml")
        )

    def test_production_kustomization_exists(self):
        """production-kustomization.yaml must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.DEMO_DIR, "production-kustomization.yaml")
        )

    def test_base_deployment_exists(self):
        """base/deployment.yaml must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.DEMO_DIR, "base", "deployment.yaml")
        )

    def test_base_service_exists(self):
        """base/service.yaml must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.DEMO_DIR, "base", "service.yaml")
        )

    def test_base_kustomization_exists(self):
        """base/kustomization.yaml must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.DEMO_DIR, "base", "kustomization.yaml")
        )

    def test_base_configmap_exists(self):
        """base/configmap.yaml must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.DEMO_DIR, "base", "configmap.yaml")
        )

    # ------------------------------------------------------------------
    # L1: YAML validity
    # ------------------------------------------------------------------

    def test_source_valid_yaml(self):
        """source.yaml must be valid YAML."""
        self._load_yaml(self.DEMO_DIR, "source.yaml")

    def test_staging_kustomization_valid_yaml(self):
        """staging-kustomization.yaml must be valid YAML."""
        self._load_yaml(self.DEMO_DIR, "staging-kustomization.yaml")

    def test_production_kustomization_valid_yaml(self):
        """production-kustomization.yaml must be valid YAML."""
        self._load_yaml(self.DEMO_DIR, "production-kustomization.yaml")

    # ------------------------------------------------------------------
    # L2: Source structure
    # ------------------------------------------------------------------

    def test_source_is_git_repository(self):
        """source.yaml must define a GitRepository resource."""
        data = self._load_yaml(self.DEMO_DIR, "source.yaml")
        assert isinstance(data, dict)
        kind = data.get("kind", "")
        assert (
            kind == "GitRepository"
        ), f"Source kind is '{kind}', expected 'GitRepository'"

    def test_source_has_url_and_interval(self):
        """GitRepository must specify url and interval."""
        data = self._load_yaml(self.DEMO_DIR, "source.yaml")
        spec = data.get("spec", {})
        assert "url" in spec, "GitRepository missing spec.url"
        assert "interval" in spec, "GitRepository missing spec.interval"

    # ------------------------------------------------------------------
    # L2: Kustomization structure
    # ------------------------------------------------------------------

    def test_staging_is_flux_kustomization(self):
        """Staging kustomization must be a Flux Kustomization resource."""
        data = self._load_yaml(self.DEMO_DIR, "staging-kustomization.yaml")
        assert data.get("kind") == "Kustomization"

    def test_production_is_flux_kustomization(self):
        """Production kustomization must be a Flux Kustomization resource."""
        data = self._load_yaml(self.DEMO_DIR, "production-kustomization.yaml")
        assert data.get("kind") == "Kustomization"

    def test_kustomizations_reference_different_paths(self):
        """Staging and production must reference different overlay paths."""
        staging = self._load_yaml(self.DEMO_DIR, "staging-kustomization.yaml")
        prod = self._load_yaml(self.DEMO_DIR, "production-kustomization.yaml")
        sp = staging.get("spec", {}).get("path", "")
        pp = prod.get("spec", {}).get("path", "")
        assert sp != pp, "Staging and production reference the same path"

    def test_kustomization_has_prune(self):
        """At least one kustomization must enable pruning."""
        staging = self._load_yaml(self.DEMO_DIR, "staging-kustomization.yaml")
        prod = self._load_yaml(self.DEMO_DIR, "production-kustomization.yaml")
        has_prune = staging.get("spec", {}).get("prune") or prod.get("spec", {}).get(
            "prune"
        )
        assert has_prune, "No kustomization enables pruning"

    def test_kustomization_has_health_checks(self):
        """At least one kustomization should define health checks."""
        staging = self._load_yaml(self.DEMO_DIR, "staging-kustomization.yaml")
        prod = self._load_yaml(self.DEMO_DIR, "production-kustomization.yaml")
        has_hc = (
            staging.get("spec", {}).get("healthChecks")
            or prod.get("spec", {}).get("healthChecks")
            or staging.get("spec", {}).get("wait")
            or prod.get("spec", {}).get("wait")
        )
        assert has_hc, "No kustomization defines health checks"

    # ------------------------------------------------------------------
    # L2: Overlay structure
    # ------------------------------------------------------------------

    def test_overlays_exist(self):
        """Staging and production overlay kustomization.yaml files must exist."""
        for env in ("staging", "production"):
            path = os.path.join(
                self.REPO_DIR, self.DEMO_DIR, "overlays", env, "kustomization.yaml"
            )
            assert os.path.isfile(
                path
            ), f"Overlay kustomization.yaml not found for {env}"

    def test_overlays_reference_base(self):
        """Overlay kustomization.yaml must reference the base directory."""
        for env in ("staging", "production"):
            data = self._load_yaml(self.DEMO_DIR, "overlays", env, "kustomization.yaml")
            resources = data.get("resources", [])
            bases = data.get("bases", [])
            all_refs = resources + bases
            has_base = any("base" in str(r) for r in all_refs)
            assert has_base, f"{env} overlay does not reference base directory"
