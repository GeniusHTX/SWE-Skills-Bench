"""
Test for 'gitops-workflow' skill — GitOps Workflow
Validates Flux CD GitOps configuration including GitRepository, Kustomization resources,
app deployment manifests, and proper Flux CD reconciliation setup.
"""

import os
import re
import glob
import pytest

import yaml


class TestGitopsWorkflow:
    """Tests for GitOps workflow configs in the flux2 repo."""

    REPO_DIR = "/workspace/flux2"

    def _read(self, relpath):
        full = os.path.join(self.REPO_DIR, relpath)
        with open(full, "r", errors="ignore") as f:
            return f.read()

    def _load_all_flux_docs(self):
        """Load all YAML documents from flux configuration files."""
        flux_files = [
            "clusters/production/flux-system/gotk-sync.yaml",
            "clusters/production/apps/kustomization.yaml",
            "apps/base/deployment.yaml",
            "apps/base/kustomization.yaml",
        ]
        all_docs = []
        for f in flux_files:
            path = os.path.join(self.REPO_DIR, f)
            if os.path.exists(path):
                content = self._read(f)
                docs = list(yaml.safe_load_all(content))
                all_docs.extend([d for d in docs if d])
        return all_docs

    # --- File Path Checks ---

    def test_gotk_sync_yaml_exists(self):
        """Verifies that clusters/production/flux-system/gotk-sync.yaml exists."""
        path = os.path.join(
            self.REPO_DIR, "clusters", "production", "flux-system", "gotk-sync.yaml"
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_apps_kustomization_yaml_exists(self):
        """Verifies that clusters/production/apps/kustomization.yaml exists."""
        path = os.path.join(
            self.REPO_DIR, "clusters", "production", "apps", "kustomization.yaml"
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_base_deployment_yaml_exists(self):
        """Verifies that apps/base/deployment.yaml exists."""
        path = os.path.join(self.REPO_DIR, "apps", "base", "deployment.yaml")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_base_kustomization_yaml_exists(self):
        """Verifies that apps/base/kustomization.yaml exists."""
        path = os.path.join(self.REPO_DIR, "apps", "base", "kustomization.yaml")
        assert os.path.exists(path), f"Expected file not found: {path}"

    # --- Semantic Checks ---

    def test_sem_all_yaml_parseable(self):
        """All flux YAML files are parseable and produce documents."""
        all_docs = self._load_all_flux_docs()
        assert len(all_docs) > 0, "No YAML documents loaded from flux config files"

    def test_sem_has_source_toolkit_api_version(self):
        """At least one doc has apiVersion starting with 'source.toolkit.fluxcd.io'."""
        all_docs = self._load_all_flux_docs()
        assert any(
            d.get("apiVersion", "").startswith("source.toolkit.fluxcd.io")
            for d in all_docs
        ), "No document with source.toolkit.fluxcd.io apiVersion"

    def test_sem_has_kustomize_toolkit_api_version(self):
        """At least one doc has apiVersion starting with 'kustomize.toolkit.fluxcd.io'."""
        all_docs = self._load_all_flux_docs()
        assert any(
            d.get("apiVersion", "").startswith("kustomize.toolkit.fluxcd.io")
            for d in all_docs
        ), "No document with kustomize.toolkit.fluxcd.io apiVersion"

    def test_sem_has_flux_kustomization_docs(self):
        """At least one Kustomization doc with fluxcd.io apiVersion exists."""
        all_docs = self._load_all_flux_docs()
        kustomization_docs = [
            d
            for d in all_docs
            if d.get("kind") == "Kustomization"
            and "fluxcd.io" in d.get("apiVersion", "")
        ]
        assert len(kustomization_docs) >= 1, "No Flux Kustomization documents found"

    def test_sem_kustomization_count(self):
        """len(kustomization_docs) >= 1."""
        all_docs = self._load_all_flux_docs()
        kustomization_docs = [
            d
            for d in all_docs
            if d.get("kind") == "Kustomization"
            and "fluxcd.io" in d.get("apiVersion", "")
        ]
        assert len(kustomization_docs) >= 1

    # --- Functional Checks ---

    def test_func_git_repository_url_not_empty(self):
        """GitRepository spec.url is not empty."""
        all_docs = self._load_all_flux_docs()
        gitrepo = next((d for d in all_docs if d.get("kind") == "GitRepository"), None)
        assert gitrepo is not None, "No GitRepository document found"
        assert gitrepo["spec"]["url"] != "", "GitRepository spec.url is empty"

    def test_func_kustomization_prune_true(self):
        """Kustomization spec.prune == True."""
        all_docs = self._load_all_flux_docs()
        kustomization_docs = [
            d
            for d in all_docs
            if d.get("kind") == "Kustomization"
            and "fluxcd.io" in d.get("apiVersion", "")
        ]
        assert len(kustomization_docs) >= 1
        kust = kustomization_docs[0]
        assert (
            kust["spec"]["prune"] is True
        ), f"spec.prune is {kust['spec'].get('prune')}, expected True"

    def test_func_kustomization_interval_reasonable(self):
        """Kustomization spec.interval is <= 10 minutes."""
        all_docs = self._load_all_flux_docs()
        kustomization_docs = [
            d
            for d in all_docs
            if d.get("kind") == "Kustomization"
            and "fluxcd.io" in d.get("apiVersion", "")
        ]
        assert len(kustomization_docs) >= 1
        kust = kustomization_docs[0]
        interval = kust["spec"]["interval"]
        valid_intervals = [
            "1m",
            "2m",
            "3m",
            "5m",
            "10m",
            "1m0s",
            "2m0s",
            "5m0s",
            "10m0s",
        ]
        match = re.match(r"(\d+)m", str(interval))
        assert (
            match and int(match.group(1)) <= 10
        ), f"Interval {interval} exceeds 10 minutes"

    def test_func_kustomization_source_ref_kind(self):
        """Kustomization spec.sourceRef.kind == 'GitRepository'."""
        all_docs = self._load_all_flux_docs()
        kustomization_docs = [
            d
            for d in all_docs
            if d.get("kind") == "Kustomization"
            and "fluxcd.io" in d.get("apiVersion", "")
        ]
        assert len(kustomization_docs) >= 1
        kust = kustomization_docs[0]
        assert kust["spec"]["sourceRef"]["kind"] == "GitRepository"

    def test_func_git_repository_has_branch_or_tag(self):
        """GitRepository spec.ref has branch or tag set."""
        all_docs = self._load_all_flux_docs()
        gitrepo = next((d for d in all_docs if d.get("kind") == "GitRepository"), None)
        assert gitrepo is not None
        ref = gitrepo["spec"].get("ref", {})
        has_branch = ref.get("branch")
        has_tag = ref.get("tag")
        assert (
            has_branch or has_tag
        ), "GitRepository spec.ref has neither branch nor tag"

    def test_func_all_flux_resources_have_namespace(self):
        """All Kustomization/GitRepository resources have metadata.namespace."""
        all_docs = self._load_all_flux_docs()
        for d in all_docs:
            if d.get("kind") in ["Kustomization", "GitRepository"]:
                ns = d.get("metadata", {}).get("namespace")
                assert ns, f"{d.get('kind')} missing metadata.namespace"

    def test_func_has_helm_release_or_deployment(self):
        """All docs contain HelmRelease or Deployment kind."""
        all_docs = self._load_all_flux_docs()
        has_helm = any(d.get("kind") == "HelmRelease" for d in all_docs)
        has_deploy = any(d.get("kind") == "Deployment" for d in all_docs)
        assert has_helm or has_deploy, "Neither HelmRelease nor Deployment found"

    def test_func_app_deployment_exists(self):
        """At least one Deployment document exists in the configs."""
        all_docs = self._load_all_flux_docs()
        app_deployment = next(
            (d for d in all_docs if d.get("kind") == "Deployment"), None
        )
        assert app_deployment is not None, "No Deployment document found"

    def test_func_failure_no_missing_kustomization(self):
        """Verify Kustomization resources are not missing from the flux-system dir."""
        path = os.path.join(
            self.REPO_DIR, "clusters", "production", "flux-system", "gotk-sync.yaml"
        )
        assert os.path.exists(
            path
        ), "gotk-sync.yaml missing — Kustomization resource may be absent"
        content = self._read("clusters/production/flux-system/gotk-sync.yaml")
        docs = [d for d in yaml.safe_load_all(content) if d]
        kust_found = any(d.get("kind") == "Kustomization" for d in docs)
        assert kust_found, "No Kustomization resource in gotk-sync.yaml"
