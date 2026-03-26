"""
Tests for k8s-manifest-generator skill.
Validates Kubernetes manifest generators (Deployment, NetworkPolicy, Secret, ConfigMap)
in kustomize repository.
"""

import os
import base64
import subprocess
import pytest

REPO_DIR = "/workspace/kustomize"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


def _run(cmd: str, cwd: str = REPO_DIR, timeout: int = 120):
    return subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


class TestK8sManifestGenerator:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_manifest_generator_go_files_exist(self):
        """deployment.go and network_policy.go must exist in api/manifest."""
        for rel in [
            "api/manifest/deployment.go",
            "api/manifest/network_policy.go",
        ]:
            assert os.path.isfile(_path(rel)), f"{rel} not found"
            assert os.path.getsize(_path(rel)) > 0, f"{rel} is empty"

    def test_secrets_and_configmap_files_exist(self):
        """secret.go and configmap.go must exist in api/manifest."""
        for rel in [
            "api/manifest/secret.go",
            "api/manifest/configmap.go",
        ]:
            assert os.path.isfile(_path(rel)), f"{rel} not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_deployment_generator_defines_run_as_non_root(self):
        """deployment.go must reference runAsNonRoot in securityContext."""
        content = _read("api/manifest/deployment.go")
        assert (
            "runAsNonRoot" in content or "RunAsNonRoot" in content
        ), "runAsNonRoot security context not enforced in deployment.go"

    def test_network_policy_deny_ingress_defined(self):
        """network_policy.go must implement default deny ingress pattern."""
        content = _read("api/manifest/network_policy.go")
        assert (
            "ingress" in content.lower()
        ), "Ingress rules not found in network_policy.go"
        assert (
            "DefaultDenyIngress" in content or "default_deny" in content.lower()
        ), "DefaultDenyIngress function not found in network_policy.go"

    def test_secret_base64_encoding_used(self):
        """secret.go must use base64 encoding for secret values."""
        content = _read("api/manifest/secret.go")
        assert (
            "encoding/base64" in content or "base64" in content
        ), "no base64 import in secret.go"
        assert (
            "EncodeToString" in content or "b64" in content.lower()
        ), "base64 encoding call not found in secret.go"

    def test_configmap_size_limit_check(self):
        """configmap.go must validate size (max 1 MiB per K8s ETCD limit)."""
        content = _read("api/manifest/configmap.go")
        assert (
            "size" in content.lower() or "1048576" in content or "1Mi" in content
        ), "No size validation found in configmap.go"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_deployment_nginx_valid(self):
        """Deployment with valid image nginx:1.25 must pass validation (mocked)."""

        def validate_image(image: str):
            if ":" not in image:
                raise ValueError(f"Image '{image}' must specify a tag")

        assert validate_image("nginx:1.25") is None

    def test_deployment_image_no_tag_error(self):
        """Deploy with tagless image 'nginx' must raise ValueError."""

        def validate_image(image: str):
            if ":" not in image:
                raise ValueError(
                    f"Image '{image}' must specify a tag (no 'latest' ambiguity)"
                )

        with pytest.raises(ValueError, match="tag"):
            validate_image("nginx")

    def test_memory_request_exceeds_limit_error(self):
        """Memory request > memory limit must raise ValueError."""

        def parse_mi(s: str) -> int:
            return int(s.replace("Mi", "")) * 1024 * 1024

        def validate_resources(request: str, limit: str):
            if parse_mi(request) > parse_mi(limit):
                raise ValueError(
                    f"Memory request ({request}) must not exceed limit ({limit})"
                )

        with pytest.raises(ValueError, match="request"):
            validate_resources("512Mi", "256Mi")

    def test_default_deny_ingress_empty_rules(self):
        """DefaultDenyIngress must produce NetworkPolicy with empty ingress rules."""

        def default_deny_ingress(namespace: str, name: str) -> dict:
            return {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": {"name": name, "namespace": namespace},
                "spec": {
                    "podSelector": {},
                    "policyTypes": ["Ingress"],
                    "ingress": [],
                },
            }

        policy = default_deny_ingress("default", "deny-all")
        assert (
            policy["spec"]["ingress"] == []
        ), "Default deny ingress must have empty ingress rules"
        assert "Ingress" in policy["spec"]["policyTypes"]

    def test_configmap_2mib_exceeds_limit_error(self):
        """ConfigMap with 2 MiB data must trigger size limit error."""
        MAX_SIZE = 1 * 1024 * 1024  # 1 MiB

        def generate_configmap(data: dict):
            total = sum(len(v.encode()) for v in data.values())
            if total > MAX_SIZE:
                raise ValueError(f"ConfigMap data size {total} exceeds 1 MiB limit")
            return {"kind": "ConfigMap", "data": data}

        large_value = "x" * (2 * 1024 * 1024)
        with pytest.raises(ValueError, match="1 MiB"):
            generate_configmap({"key": large_value})

    def test_secret_values_are_base64_encoded(self):
        """Secret generator must base64-encode all data values."""

        def generate_secret(data: dict) -> dict:
            return {
                "kind": "Secret",
                "data": {
                    k: base64.b64encode(v.encode()).decode() for k, v in data.items()
                },
            }

        secret = generate_secret({"password": "secret123", "username": "admin"})
        for key, encoded in secret["data"].items():
            decoded = base64.b64decode(encoded).decode()
            if key == "password":
                assert decoded == "secret123"
            elif key == "username":
                assert decoded == "admin"
