"""
Test for 'k8s-manifest-generator' skill — Kubernetes Manifest Generator (Go)
Validates DeploymentBuilder, HPABuilder, NetworkPolicyBuilder, label
consistency, resource requests/limits validation, and Go source patterns.
"""

import glob
import os
import re

import pytest


class TestK8sManifestGenerator:
    """Verify K8s manifest generator via static Go source inspection."""

    REPO_DIR = "/workspace/kustomize"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _k8s(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "k8s", *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_go_mod_exists(self):
        """go.mod must exist at repo root."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, "go.mod")), "go.mod not found"

    def test_deployment_go_exists(self):
        """k8s/deployment.go must exist."""
        path = self._k8s("deployment.go")
        alt = os.path.join(self.REPO_DIR, "manifests", "deployment.go")
        assert os.path.isfile(path) or os.path.isfile(alt), "deployment.go not found"

    def test_hpa_and_network_policy_exist(self):
        """k8s/hpa.go and k8s/network_policy.go must exist."""
        assert os.path.isfile(self._k8s("hpa.go")), "hpa.go not found"
        assert os.path.isfile(self._k8s("network_policy.go")), "network_policy.go not found"

    def test_test_files_exist(self):
        """At least one *_test.go must exist in k8s/."""
        tests = glob.glob(self._k8s("*_test.go"))
        assert len(tests) >= 1, "No *_test.go in k8s/"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_deployment_build_method(self):
        """DeploymentBuilder must have Build() returning Deployment."""
        content = self._read_file(self._k8s("deployment.go"))
        if not content:
            pytest.skip("deployment.go not found")
        assert "DeploymentBuilder" in content
        assert "Build(" in content
        assert "Deployment" in content

    def test_hpa_min_max_validation(self):
        """HPABuilder must validate minReplicas <= maxReplicas."""
        content = self._read_file(self._k8s("hpa.go"))
        if not content:
            pytest.skip("hpa.go not found")
        has_min = "min" in content.lower() and "max" in content.lower()
        has_error = "error" in content.lower() or "Error" in content
        assert has_min and has_error, "min/max validation not found"

    def test_label_consistency_validator(self):
        """Label consistency validation must check selector matches labels."""
        content = ""
        for name in glob.glob(self._k8s("*.go")):
            content += self._read_file(name)
        has_label = "Label" in content or "label" in content
        has_selector = "selector" in content or "matchLabels" in content
        assert has_label and has_selector, "Label/selector consistency check not found"

    def test_resource_requests_limits_check(self):
        """DeploymentBuilder must validate requests <= limits."""
        content = self._read_file(self._k8s("deployment.go"))
        if not content:
            pytest.skip("deployment.go not found")
        has_req = "Requests" in content or "requests" in content
        has_lim = "Limits" in content or "limits" in content
        assert has_req and has_lim, "Resource requests/limits not found"

    def test_go_mod_version_at_least_1_21(self):
        """go.mod must declare go >= 1.21."""
        content = self._read_file(os.path.join(self.REPO_DIR, "go.mod"))
        if not content:
            pytest.skip("go.mod not found")
        m = re.search(r"^go\s+1\.(\d+)", content, re.MULTILINE)
        assert m, "go version directive not found"
        assert int(m.group(1)) >= 21, f"go 1.{m.group(1)} < 1.21"

    # ── functional_check (static Go) ─────────────────────────────────────

    def test_deployment_uses_apps_v1(self):
        """deployment.go must use apps/v1, not extensions/v1beta1."""
        content = self._read_file(self._k8s("deployment.go"))
        if not content:
            pytest.skip("deployment.go not found")
        has_v1 = "apps/v1" in content or "appsv1" in content
        assert has_v1, "apps/v1 apiVersion not found"
        assert "extensions/v1beta1" not in content, "Deprecated extensions/v1beta1 used"

    def test_hpa_min_max_test_case(self):
        """Test file must contain HPA min > max validation error test."""
        test_files = glob.glob(self._k8s("*_test.go"))
        for tf in test_files:
            content = self._read_file(tf)
            if "HPA" in content or "hpa" in content:
                has_error = "err" in content and ("min" in content.lower() or "max" in content.lower())
                assert has_error, "HPA validation error test not found"
                return
        pytest.fail("No HPA test file found")

    def test_deployment_zero_replicas_accepted(self):
        """DeploymentBuilder must accept replicas=0 (scale-to-zero)."""
        content = self._read_file(self._k8s("deployment.go"))
        if not content:
            pytest.skip("deployment.go not found")
        # If replicas validation exists, it must reject negative, not zero
        if "Replicas" in content and "<" in content:
            assert "< 0" in content or "<= 0" not in content
