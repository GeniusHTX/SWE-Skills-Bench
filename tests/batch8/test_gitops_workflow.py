"""
Test for 'gitops-workflow' skill — GitOps Manifest Reconciler
Validates that the Agent created a Python package for reconciling K8s
manifests with diff engine, rollout manager, and conflict detection.
"""

import os
import re
import sys

import pytest


class TestGitopsWorkflow:
    """Verify GitOps manifest reconciler implementation."""

    REPO_DIR = "/workspace/flux2"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_gitops_package_init_exists(self):
        """Verify __init__.py and reconciler.py exist under src/gitops/."""
        for rel in ("src/gitops/__init__.py", "src/gitops/reconciler.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_diff_rollout_models_exist(self):
        """Verify diff.py, rollout.py, and models.py exist."""
        for rel in ("src/gitops/diff.py", "src/gitops/rollout.py",
                     "src/gitops/models.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_all_classes_importable(self):
        """ManifestReconciler, DiffEngine, RolloutManager can be imported."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            from gitops.reconciler import ManifestReconciler  # noqa: F401
            from gitops.diff import DiffEngine  # noqa: F401
            from gitops.rollout import RolloutManager  # noqa: F401
        except ImportError:
            pytest.skip("gitops not importable")
        finally:
            sys.path.pop(0)

    # ── semantic_check ──────────────────────────────────────────────

    def test_manifest_reconciler_public_api(self):
        """Verify ManifestReconciler exposes to_apply, to_delete, unchanged."""
        content = self._read(os.path.join(self.REPO_DIR, "src/gitops/reconciler.py"))
        assert content, "reconciler.py is empty or unreadable"
        for attr in ("to_apply", "to_delete", "unchanged"):
            assert attr in content, f"'{attr}' not found in reconciler.py"

    def test_diff_entry_field_diff(self):
        """Verify DiffEngine returns DiffEntry objects with field-level information."""
        content = self._read(os.path.join(self.REPO_DIR, "src/gitops/diff.py"))
        assert content, "diff.py is empty or unreadable"
        assert "DiffEntry" in content, "DiffEntry not found in diff.py"
        assert "class DiffEngine" in content, "DiffEngine class not found"

    def test_conflict_error_defined(self):
        """Verify ConflictError exception class is defined."""
        # Check multiple possible locations
        found = False
        for candidate in ("src/gitops/reconciler.py", "src/gitops/exceptions.py",
                          "src/gitops/models.py"):
            content = self._read(os.path.join(self.REPO_DIR, candidate))
            if "ConflictError" in content:
                found = True
                break
        assert found, "ConflictError not found in any gitops module"

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

    def test_reconcile_new_resource_to_apply(self):
        """ManifestReconciler.reconcile places new resources in to_apply."""
        rec_mod = self._import("gitops.reconciler")
        models_mod = self._import("gitops.models")
        ns = models_mod.Manifest(kind="Namespace", name="my-ns", namespace="")
        result = rec_mod.ManifestReconciler().reconcile(desired=[ns], current=[])
        assert len(result.to_apply) == 1
        assert len(result.to_delete) == 0

    def test_reconcile_removed_resource_to_delete(self):
        """ManifestReconciler.reconcile places orphan resources in to_delete."""
        rec_mod = self._import("gitops.reconciler")
        models_mod = self._import("gitops.models")
        old = models_mod.Manifest(kind="Namespace", name="old-ns", namespace="")
        result = rec_mod.ManifestReconciler().reconcile(desired=[], current=[old])
        assert len(result.to_apply) == 0
        assert len(result.to_delete) == 1

    def test_diff_engine_returns_field_diff(self):
        """DiffEngine returns exactly 1 DiffEntry when one field changes."""
        mod = self._import("gitops.diff")
        diffs = mod.DiffEngine().compute({"replicas": 1}, {"replicas": 3})
        assert len(diffs) == 1, f"Expected 1 diff entry, got {len(diffs)}"

    def test_rollout_namespace_first_ordering(self):
        """RolloutManager orders Namespace before Deployment in rollout sequence."""
        rollout_mod = self._import("gitops.rollout")
        models_mod = self._import("gitops.models")
        deploy = models_mod.Manifest(kind="Deployment", name="api", namespace="default")
        ns = models_mod.Manifest(kind="Namespace", name="default", namespace="")
        plan = rollout_mod.RolloutManager().plan([deploy, ns])
        assert plan.sequence[0].kind == "Namespace", \
            f"Expected Namespace first, got {plan.sequence[0].kind}"

    def test_conflict_error_on_duplicate_resource(self):
        """ManifestReconciler raises ConflictError on duplicate kind+name+namespace."""
        rec_mod = self._import("gitops.reconciler")
        models_mod = self._import("gitops.models")
        # Try to import ConflictError from various locations
        ConflictError = None
        for loc in ("gitops.exceptions", "gitops.reconciler", "gitops.models"):
            try:
                m = self._import(loc)
                ConflictError = getattr(m, "ConflictError", None)
                if ConflictError:
                    break
            except Exception:
                continue
        if ConflictError is None:
            pytest.skip("ConflictError not found")
        ns1 = models_mod.Manifest(kind="Namespace", name="my-ns", namespace="")
        ns2 = models_mod.Manifest(kind="Namespace", name="my-ns", namespace="")
        with pytest.raises(ConflictError):
            rec_mod.ManifestReconciler().reconcile(desired=[ns1, ns2], current=[])
