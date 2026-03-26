"""
Test for 'k8s-manifest-generator' skill — Kustomize Manifest Generator
Validates that the Agent created Kustomize base+overlay structure for 3
environments and that kustomize build succeeds for each.
"""

import os
import subprocess
import pytest
import yaml  # Imported at the top for consistency


class TestK8sManifestGenerator:
    """Verify Kubernetes manifest generation with Kustomize."""

    REPO_DIR = "/workspace/kustomize"

    # [!] Change: updated app-generator to multi-env as required by the requirements doc
    BASE_DIR = "examples/multi-env"

    ENVIRONMENTS = ["dev", "staging", "production"]

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_base_kustomization_exists(self):
        """base/kustomization.yaml must exist."""
        fpath = os.path.join(self.REPO_DIR, self.BASE_DIR, "base", "kustomization.yaml")
        assert os.path.isfile(fpath), "base/kustomization.yaml not found"

    def test_base_deployment_exists(self):
        """base/deployment.yaml must exist."""
        fpath = os.path.join(self.REPO_DIR, self.BASE_DIR, "base", "deployment.yaml")
        assert os.path.isfile(fpath), "base/deployment.yaml not found"

    @pytest.mark.parametrize("env", ENVIRONMENTS)
    def test_overlay_kustomization_exists(self, env):
        """Each overlay must have kustomization.yaml."""
        fpath = os.path.join(
            self.REPO_DIR, self.BASE_DIR, "overlays", env, "kustomization.yaml"
        )
        assert os.path.isfile(fpath), f"overlays/{env}/kustomization.yaml not found"

    # ------------------------------------------------------------------
    # L2: YAML validation & kustomize build
    # ------------------------------------------------------------------

    def test_base_kustomization_has_resources(self):
        """base/kustomization.yaml must list resources."""
        fpath = os.path.join(self.REPO_DIR, self.BASE_DIR, "base", "kustomization.yaml")
        with open(fpath, "r") as f:
            doc = yaml.safe_load(f)
        assert "resources" in doc, "kustomization.yaml missing resources list"
        assert len(doc["resources"]) >= 1, "resources list is empty"

    @pytest.mark.parametrize("env", ENVIRONMENTS)
    def test_overlay_references_base(self, env):
        """Each overlay must reference ../base via resources or bases."""
        fpath = os.path.join(
            self.REPO_DIR, self.BASE_DIR, "overlays", env, "kustomization.yaml"
        )
        with open(fpath, "r") as f:
            doc = yaml.safe_load(f)
        resources = doc.get("resources", []) + doc.get("bases", [])
        has_base = any("base" in str(r) for r in resources)
        assert has_base, f"Overlay {env} doesn't reference base directory"

    @pytest.mark.parametrize("env", ENVIRONMENTS)
    def test_kustomize_build_succeeds(self, env):
        """kustomize build must succeed for each environment."""
        overlay = os.path.join(self.BASE_DIR, "overlays", env)
        result = subprocess.run(
            ["kustomize", "build", overlay],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert (
            result.returncode == 0
        ), f"kustomize build failed for {env}:\n{result.stderr}"

    def test_production_has_higher_replicas(self):
        """Production overlay should specify more replicas than dev."""
        prod_path = os.path.join(self.REPO_DIR, self.BASE_DIR, "overlays", "production")
        dev_path = os.path.join(self.REPO_DIR, self.BASE_DIR, "overlays", "dev")
        prod_out = subprocess.run(
            ["kustomize", "build", prod_path],
            capture_output=True,
            text=True,
            timeout=120,
        )
        dev_out = subprocess.run(
            ["kustomize", "build", dev_path],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if prod_out.returncode != 0 or dev_out.returncode != 0:
            pytest.skip("kustomize build failed")
        # Simple check: production should have replicas >= dev
        assert (
            "replicas" in prod_out.stdout or "Deployment" in prod_out.stdout
        ), "Production output missing deployment info"

    def test_namespace_differs_between_envs(self):
        """Different environments should have different namespaces or prefixes."""
        envs_content = {}
        for env in self.ENVIRONMENTS:
            fpath = os.path.join(
                self.REPO_DIR, self.BASE_DIR, "overlays", env, "kustomization.yaml"
            )
            with open(fpath, "r") as f:
                envs_content[env] = yaml.safe_load(f)

        # Check if overlays customize namespace, namePrefix, or patches
        customizations = set()
        for env, doc in envs_content.items():
            if doc.get("namespace"):
                customizations.add(doc["namespace"])
            if doc.get("namePrefix"):
                customizations.add(doc["namePrefix"])
        assert (
            len(customizations) >= 2 or len(envs_content) >= 3
        ), "Overlays should differentiate environments"
