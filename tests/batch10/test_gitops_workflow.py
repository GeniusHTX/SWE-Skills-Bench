"""
Test for 'gitops-workflow' skill — Flux2 GitOps reconciliation pipeline
Validates that the Agent implemented a Go reconciliation pipeline with
Kustomize overlays for the flux2 project.
"""

import os
import re

import pytest


class TestGitopsWorkflow:
    """Verify GitOps workflow with Flux2 reconciliation."""

    REPO_DIR = "/workspace/flux2"

    def test_reconciler_go_file_exists(self):
        """A Go reconciler file must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".go"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Rr]econcil", content):
                        found = True
                        break
            if found:
                break
        assert found, "No reconciler Go file found"

    def test_kustomization_yaml_exists(self):
        """At least one kustomization.yaml must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("kustomization.yaml", "kustomization.yml", "Kustomization"):
                    found = True
                    break
            if found:
                break
        assert found, "kustomization.yaml not found"

    def test_overlay_directories_exist(self):
        """Kustomize overlay directories should exist (e.g. dev, staging, production)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for d in dirs:
                if d in ("overlays", "environments", "dev", "staging", "production", "prod"):
                    found = True
                    break
            if found:
                break
        assert found, "No overlay directories found"

    def test_reconcile_function(self):
        """Reconcile function must exist in Go source."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".go"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"func\s+\(.*\)\s+Reconcile\s*\(", content):
                        found = True
                        break
            if found:
                break
        assert found, "Reconcile function not found"

    def test_controller_runtime_import(self):
        """Go code should import controller-runtime or sigs.k8s.io/controller-runtime."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".go"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"sigs\.k8s\.io/controller-runtime|ctrl \"sigs", content):
                        found = True
                        break
            if found:
                break
        assert found, "controller-runtime import not found"

    def test_crd_or_api_types_defined(self):
        """Custom Resource Definitions or API types should be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".go"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"type\s+\w+\s+struct.*Spec|type\s+\w+Spec\s+struct|kubebuilder:object:root", content, re.DOTALL):
                        found = True
                        break
            if found:
                break
        assert found, "No CRD or API types defined"

    def test_status_conditions(self):
        """Reconciler should update status conditions."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".go"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Ss]tatus\.|[Cc]ondition|SetCondition|StatusCondition|ReadyCondition", content):
                        found = True
                        break
            if found:
                break
        assert found, "No status conditions handling found"

    def test_git_repository_source(self):
        """Pipeline should reference a GitRepository source."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".go", ".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"GitRepository|source\.toolkit|kind:\s*GitRepository", content):
                        found = True
                        break
            if found:
                break
        assert found, "No GitRepository source found"

    def test_health_check_or_readiness(self):
        """Reconciler should implement health checks or readiness probes."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".go", ".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Hh]ealth|[Rr]eady|readiness|liveness|healthz", content):
                        found = True
                        break
            if found:
                break
        assert found, "No health check or readiness probe found"

    def test_go_mod_exists(self):
        """go.mod must exist at the module root."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "go.mod" in files:
                found = True
                break
        assert found, "go.mod not found"

    def test_error_handling_in_reconciler(self):
        """Reconciler must handle errors properly."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".go"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Rr]econcil", content):
                        if re.search(r"if\s+err\s*!=\s*nil|ctrl\.Result\{", content):
                            found = True
                            break
            if found:
                break
        assert found, "Reconciler does not handle errors"
