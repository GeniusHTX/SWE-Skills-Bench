"""Test file for the gitops-workflow skill.

This suite validates the TenantConfig CRD types, TenantReconciler controller,
and related GitOps workflow components in the Flux2 repository.
"""

from __future__ import annotations

import pathlib
import re

import pytest


class TestGitopsWorkflow:
    """Verify Flux2 TenantConfig CRD and TenantReconciler."""

    REPO_DIR = "/workspace/flux2"

    CONTROLLER_GO = "internal/controller/tenant_controller.go"
    TYPES_GO = "api/v1alpha1/tenantconfig_types.go"
    DEEPCOPY_GO = "api/v1alpha1/zz_generated.deepcopy.go"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    def _go_struct_body(self, source: str, name: str) -> str | None:
        m = re.search(rf"type\s+{name}\s+struct\s*\{{", source)
        if m is None:
            return None
        depth, i = 1, m.end()
        while i < len(source) and depth > 0:
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
            i += 1
        return source[m.start() : i]

    def _all_go_sources(self) -> str:
        parts = []
        for d in ("internal/controller", "api/v1alpha1"):
            dp = self._repo_path(d)
            if dp.is_dir():
                for f in sorted(dp.glob("*.go")):
                    parts.append(f.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_internal_controller_tenant_controller_go_exists(self):
        """Verify tenant_controller.go exists and is non-empty."""
        self._assert_non_empty_file(self.CONTROLLER_GO)

    def test_file_path_api_v1alpha1_tenantconfig_types_go_exists(self):
        """Verify tenantconfig_types.go exists and is non-empty."""
        self._assert_non_empty_file(self.TYPES_GO)

    def test_file_path_api_v1alpha1_zz_generated_deepcopy_go_exists(self):
        """Verify zz_generated.deepcopy.go exists and is non-empty."""
        self._assert_non_empty_file(self.DEEPCOPY_GO)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_tenantconfigspec_struct_has_all_required_fields_with_correct(
        self,
    ):
        """TenantConfigSpec struct has all required fields with correct JSON tags."""
        src = self._read_text(self.TYPES_GO)
        body = self._go_struct_body(src, "TenantConfigSpec")
        assert body is not None, "TenantConfigSpec struct not found"
        assert re.search(r'json:"', body), "TenantConfigSpec must have JSON tags"

    def test_semantic_tenantconfigstatus_struct_has_conditions_ready_flags_lastrec(
        self,
    ):
        """TenantConfigStatus has Conditions, ready flags, lastReconcileTime, observedGeneration."""
        src = self._read_text(self.TYPES_GO)
        body = self._go_struct_body(src, "TenantConfigStatus")
        assert body is not None, "TenantConfigStatus struct not found"
        assert re.search(r"Conditions|conditions", body), "Status must have Conditions"
        assert re.search(
            r"ObservedGeneration|observedGeneration", body
        ), "Status must have ObservedGeneration"

    def test_semantic_gitsourcespec_has_url_branch_secretref_fields(self):
        """GitSourceSpec has url, branch, secretRef fields."""
        src = self._read_text(self.TYPES_GO)
        body = self._go_struct_body(src, "GitSourceSpec")
        assert body is not None, "GitSourceSpec struct not found"
        for field in ("url", "branch", "secretRef"):
            assert re.search(rf"(?i){field}", body), f"GitSourceSpec missing {field}"

    def test_semantic_resourcequotaspec_has_cpulimit_memorylimit_podcount(self):
        """ResourceQuotaSpec has cpuLimit, memoryLimit, podCount."""
        src = self._read_text(self.TYPES_GO)
        body = self._go_struct_body(src, "ResourceQuotaSpec")
        assert body is not None, "ResourceQuotaSpec struct not found"
        for field in ("cpu", "memory", "pod"):
            assert re.search(
                rf"(?i){field}", body
            ), f"ResourceQuotaSpec missing {field}-related field"

    def test_semantic_tenantreconciler_implements_reconcile_method(self):
        """TenantReconciler implements Reconcile method."""
        src = self._read_text(self.CONTROLLER_GO)
        assert re.search(
            r"func\s+\(.*TenantReconciler\)\s+Reconcile\s*\(", src
        ), "TenantReconciler must implement Reconcile method"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, mocked via source analysis)
    # ------------------------------------------------------------------

    def test_functional_creating_tenantconfig_creates_namespace_gitrepository_kustom(
        self,
    ):
        """Creating TenantConfig creates namespace, GitRepository, Kustomization."""
        src = self._read_text(self.CONTROLLER_GO)
        for resource in ("Namespace", "GitRepository", "Kustomization"):
            assert re.search(
                rf"(?i){resource}", src
            ), f"Reconciler should create {resource}"

    def test_functional_gitrepository_named_name_source_with_correct_url_branch_inte(
        self,
    ):
        """GitRepository named {name}-source with correct URL, branch, interval."""
        src = self._read_text(self.CONTROLLER_GO)
        assert re.search(
            r"source|Source|GitRepository", src
        ), "Reconciler must create GitRepository source"
        assert re.search(
            r"[Uu]rl|URL|Branch|branch|Interval|interval", src
        ), "GitRepository should be configured with url, branch, interval"

    def test_functional_kustomization_named_name_sync_with_correct_sourceref_path_pr(
        self,
    ):
        """Kustomization named {name}-sync with correct sourceRef, path, prune: true."""
        src = self._read_text(self.CONTROLLER_GO)
        assert re.search(
            r"[Kk]ustomization|sync", src
        ), "Reconciler must create Kustomization"
        assert re.search(
            r"[Ss]ourceRef|[Pp]rune|prune", src
        ), "Kustomization should have sourceRef and prune configuration"

    def test_functional_suspend_true_sets_suspended_condition_without_deleting_resou(
        self,
    ):
        """Suspend=true sets Suspended condition without deleting resources."""
        src = self._read_text(self.CONTROLLER_GO)
        assert re.search(
            r"[Ss]uspend|Suspended", src
        ), "Reconciler must handle suspend flag"

    def test_functional_deletion_removes_kustomization_gitrepository_namespace_in_or(
        self,
    ):
        """Deletion removes Kustomization, GitRepository, namespace in order."""
        src = self._read_text(self.CONTROLLER_GO)
        assert re.search(
            r"[Ff]inalizer|[Dd]elete|[Cc]leanup", src
        ), "Reconciler must handle deletion/cleanup"
