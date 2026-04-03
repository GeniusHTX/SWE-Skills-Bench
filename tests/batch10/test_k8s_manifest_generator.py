"""
Test for 'k8s-manifest-generator' skill — Kustomize manifest generator
Validates that the Agent created Kubernetes manifests using Kustomize
for the kustomize project.
"""

import os
import re

import pytest


class TestK8sManifestGenerator:
    """Verify Kubernetes manifest generation with Kustomize."""

    REPO_DIR = "/workspace/kustomize"

    def test_kustomization_yaml_exists(self):
        """kustomization.yaml must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("kustomization.yaml", "kustomization.yml"):
                    found = True
                    break
            if found:
                break
        assert found, "kustomization.yaml not found"

    def test_deployment_manifest_exists(self):
        """A Deployment manifest must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"kind:\s*Deployment", content):
                        found = True
                        break
            if found:
                break
        assert found, "No Deployment manifest found"

    def test_service_manifest_exists(self):
        """A Service manifest must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"kind:\s*Service", content):
                        found = True
                        break
            if found:
                break
        assert found, "No Service manifest found"

    def test_namespace_defined(self):
        """Manifests must define or reference a namespace."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"namespace:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No namespace defined in manifests"

    def test_configmap_or_secret(self):
        """ConfigMap or Secret manifest should exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"kind:\s*(ConfigMap|Secret)", content):
                        found = True
                        break
            if found:
                break
        assert found, "No ConfigMap or Secret manifest found"

    def test_kustomization_references_resources(self):
        """kustomization.yaml must list resources."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "kustomization.yaml" in files or "kustomization.yml" in files:
                fname = "kustomization.yaml" if "kustomization.yaml" in files else "kustomization.yml"
                path = os.path.join(root, fname)
                with open(path, "r", errors="ignore") as fh:
                    content = fh.read()
                if re.search(r"resources:", content):
                    found = True
                break
        assert found, "kustomization.yaml does not list resources"

    def test_labels_applied(self):
        """Manifests should apply labels for resource identification."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"labels:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No labels found in manifests"

    def test_container_image_specified(self):
        """Deployment must specify a container image."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "Deployment" in content and re.search(r"image:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No container image specified in Deployment"

    def test_ports_defined(self):
        """Service or Deployment must define ports."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"ports:", content) and re.search(r"containerPort:|port:|targetPort:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No ports defined"

    def test_overlay_or_patch(self):
        """Kustomize overlays or patches should exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"patches:|patchesStrategicMerge:|patchesJson6902:", content):
                        found = True
                        break
            if found:
                break
        if not found:
            for root, dirs, files in os.walk(self.REPO_DIR):
                for d in dirs:
                    if d in ("overlays", "patches"):
                        found = True
                        break
                if found:
                    break
        assert found, "No overlays or patches found"

    def test_replicas_configured(self):
        """Deployment should configure replicas."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "Deployment" in content and re.search(r"replicas:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No replicas configured in Deployment"
