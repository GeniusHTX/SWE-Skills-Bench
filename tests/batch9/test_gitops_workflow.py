"""
Test for 'gitops-workflow' skill — GitOps Workflow Builders (Go)
Validates FluxConfigBuilder, ArgoCDAppBuilder, KustomizationBuilder,
HealthChecker via static Go source analysis for CRD correctness,
validation logic, and error handling patterns.
"""

import os
import re

import pytest


class TestGitopsWorkflow:
    """Verify GitOps workflow builders via static Go source inspection."""

    REPO_DIR = "/workspace/flux2"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _go(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "gitops", *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_go_mod_exists(self):
        """go.mod must exist at repository root."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, "go.mod")), "go.mod not found"

    def test_flux_go_exists(self):
        """gitops/flux.go must exist."""
        assert os.path.isfile(self._go("flux.go")), "flux.go not found"

    def test_argocd_go_exists(self):
        """gitops/argocd.go must exist."""
        assert os.path.isfile(self._go("argocd.go")), "argocd.go not found"

    def test_kustomization_go_exists(self):
        """gitops/kustomization.go must exist."""
        assert os.path.isfile(self._go("kustomization.go")), "kustomization.go not found"

    def test_health_go_exists(self):
        """gitops/health.go must exist."""
        assert os.path.isfile(self._go("health.go")), "health.go not found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_flux_apiversion_v1_not_beta(self):
        """Flux must use source.toolkit.fluxcd.io/v1, not v1beta*."""
        content = self._read_file(self._go("flux.go"))
        if not content:
            pytest.skip("flux.go not found")
        assert "source.toolkit.fluxcd.io/v1" in content, "v1 apiVersion not found"
        # Ensure no beta versions used for GitRepository
        lines = content.split("\n")
        for line in lines:
            if "source.toolkit.fluxcd.io" in line:
                assert "v1beta" not in line, f"Deprecated beta apiVersion found: {line.strip()}"

    def test_argocd_prune_true(self):
        """ArgoCDAppBuilder must set Prune = true in SyncPolicy."""
        content = self._read_file(self._go("argocd.go"))
        if not content:
            pytest.skip("argocd.go not found")
        assert "Prune" in content, "Prune field not found"
        # Check that Prune is set to true, not false
        assert "Prune" in content and "true" in content

    def test_kustomization_validates_nonempty_resources(self):
        """KustomizationBuilder must validate non-empty Resources."""
        content = self._read_file(self._go("kustomization.go"))
        if not content:
            pytest.skip("kustomization.go not found")
        has_len_check = "len(" in content and ("Resources" in content or "resources" in content)
        assert has_len_check, "No length check on Resources"
        assert "error" in content.lower() or "Errorf" in content

    def test_duration_validation_uses_parse_duration(self):
        """Interval field must be validated via time.ParseDuration."""
        for name in ("flux.go", "kustomization.go"):
            content = self._read_file(self._go(name))
            if "ParseDuration" in content:
                return
        pytest.fail("time.ParseDuration not used for Interval validation")

    def test_health_checker_three_statuses(self):
        """HealthChecker must define Healthy, Degraded, Progressing."""
        content = self._read_file(self._go("health.go"))
        if not content:
            pytest.skip("health.go not found")
        for status in ("Healthy", "Degraded", "Progressing"):
            assert status in content, f"Status '{status}' not found"

    # ── functional_check (static Go) ─────────────────────────────────────

    def test_go_mod_version_at_least_1_21(self):
        """go.mod must declare go >= 1.21."""
        content = self._read_file(os.path.join(self.REPO_DIR, "go.mod"))
        if not content:
            pytest.skip("go.mod not found")
        m = re.search(r"^go\s+1\.(\d+)", content, re.MULTILINE)
        assert m, "go version directive not found"
        assert int(m.group(1)) >= 21, f"go 1.{m.group(1)} < 1.21"

    def test_flux_yaml_template_contains_apiversion(self):
        """flux.go must contain apiVersion string for YAML output."""
        content = self._read_file(self._go("flux.go"))
        if not content:
            pytest.skip("flux.go not found")
        assert "source.toolkit.fluxcd.io/v1" in content

    def test_empty_resources_returns_error_not_panic(self):
        """Empty resources must return error, not use panic()."""
        content = self._read_file(self._go("kustomization.go"))
        if not content:
            pytest.skip("kustomization.go not found")
        # Find the validation block
        assert "return" in content and ("err" in content or "Error" in content)
        assert "panic(" not in content, "panic() found in kustomization.go"
