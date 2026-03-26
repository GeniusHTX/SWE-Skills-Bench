"""
Test for 'gitops-workflow' skill — GitOps Workflow for Kubernetes
Validates that the Agent created a Flux GitOps demo with Kustomize overlays
and a verification script.
"""

import os
import subprocess
import pytest


class TestGitopsWorkflow:
    """Verify Flux GitOps demo configuration."""

    REPO_DIR = "/workspace/flux2"

    BASE_DIR = "hack/gitops-demo"

    # ------------------------------------------------------------------
    # L1: directory structure & file existence
    # ------------------------------------------------------------------

    def test_base_deployment_exists(self):
        """apps/base/deployment.yaml must exist."""
        fpath = os.path.join(
            self.REPO_DIR, self.BASE_DIR, "apps", "base", "deployment.yaml"
        )
        assert os.path.isfile(fpath), "base/deployment.yaml not found"

    def test_base_service_exists(self):
        """apps/base/service.yaml must exist."""
        fpath = os.path.join(
            self.REPO_DIR, self.BASE_DIR, "apps", "base", "service.yaml"
        )
        assert os.path.isfile(fpath), "base/service.yaml not found"

    def test_base_kustomization_exists(self):
        """apps/base/kustomization.yaml must exist."""
        fpath = os.path.join(
            self.REPO_DIR, self.BASE_DIR, "apps", "base", "kustomization.yaml"
        )
        assert os.path.isfile(fpath), "base/kustomization.yaml not found"

    def test_dev_overlay_exists(self):
        """apps/overlays/dev/kustomization.yaml must exist."""
        fpath = os.path.join(
            self.REPO_DIR,
            self.BASE_DIR,
            "apps",
            "overlays",
            "dev",
            "kustomization.yaml",
        )
        assert os.path.isfile(fpath), "dev overlay kustomization.yaml not found"

    def test_dev_patch_exists(self):
        """apps/overlays/dev/patch-replicas.yaml must exist."""
        fpath = os.path.join(
            self.REPO_DIR,
            self.BASE_DIR,
            "apps",
            "overlays",
            "dev",
            "patch-replicas.yaml",
        )
        assert os.path.isfile(fpath), "patch-replicas.yaml not found"

    def test_verify_script_exists(self):
        """hack/verify-gitops-demo.sh must exist."""
        fpath = os.path.join(self.REPO_DIR, "hack", "verify-gitops-demo.sh")
        assert os.path.isfile(fpath), "verify-gitops-demo.sh not found"

    # ------------------------------------------------------------------
    # L2: YAML content validation
    # ------------------------------------------------------------------

    def test_deployment_has_required_fields(self):
        """base/deployment.yaml must have apiVersion, kind, metadata, spec."""
        import yaml

        fpath = os.path.join(
            self.REPO_DIR, self.BASE_DIR, "apps", "base", "deployment.yaml"
        )
        with open(fpath, "r") as f:
            doc = yaml.safe_load(f)
        required = ["apiVersion", "kind", "metadata", "spec"]
        for field in required:
            assert field in doc, f"Deployment missing '{field}'"
        assert (
            doc["kind"] == "Deployment"
        ), f"Expected kind=Deployment, got {doc['kind']}"

    def test_service_has_required_fields(self):
        """base/service.yaml must have apiVersion, kind, metadata, spec."""
        import yaml

        fpath = os.path.join(
            self.REPO_DIR, self.BASE_DIR, "apps", "base", "service.yaml"
        )
        with open(fpath, "r") as f:
            doc = yaml.safe_load(f)
        assert doc.get("kind") == "Service", f"Expected kind=Service"

    def test_base_kustomization_references_files(self):
        """base kustomization.yaml must reference deployment and service."""
        import yaml

        fpath = os.path.join(
            self.REPO_DIR, self.BASE_DIR, "apps", "base", "kustomization.yaml"
        )
        with open(fpath, "r") as f:
            doc = yaml.safe_load(f)
        resources = doc.get("resources", [])
        assert "deployment.yaml" in resources, "deployment.yaml not in resources"
        assert "service.yaml" in resources, "service.yaml not in resources"

    def test_kustomize_build_succeeds(self):
        """kustomize build on dev overlay must succeed."""
        overlay_path = os.path.join(self.BASE_DIR, "apps", "overlays", "dev")
        result = subprocess.run(
            ["kustomize", "build", overlay_path],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"kustomize build failed:\n{result.stderr}"

    def test_kustomize_output_has_deployment(self):
        """kustomize build output must contain a Deployment resource."""
        overlay_path = os.path.join(self.BASE_DIR, "apps", "overlays", "dev")
        result = subprocess.run(
            ["kustomize", "build", overlay_path],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"kustomize build failed: {result.stderr[:500]}")
        assert "kind: Deployment" in result.stdout, "No Deployment in kustomize output"

    def test_kustomize_output_has_service(self):
        """kustomize build output must contain a Service resource."""
        overlay_path = os.path.join(self.BASE_DIR, "apps", "overlays", "dev")
        result = subprocess.run(
            ["kustomize", "build", overlay_path],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"kustomize build failed: {result.stderr[:500]}")
        assert "kind: Service" in result.stdout, "No Service in kustomize output"

    def test_verify_script_runs(self):
        """verify-gitops-demo.sh must run with exit code 0."""
        result = subprocess.run(
            ["bash", "hack/verify-gitops-demo.sh"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert (
            result.returncode == 0
        ), f"Verification script failed:\n{result.stdout}\n{result.stderr}"
