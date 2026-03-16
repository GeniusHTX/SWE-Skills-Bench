"""
Test for 'linkerd-patterns' skill — Linkerd Service Mesh Patterns
Validates that the Agent created mTLS verification examples with Server/
ServerAuthorization CRDs and proper Linkerd annotations.
"""

import os
import subprocess
import pytest


class TestLinkerdPatterns:
    """Verify Linkerd mTLS demonstration setup."""

    REPO_DIR = "/workspace/linkerd2"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_deployments_yaml_exists(self):
        """examples/mtls-demo/deployments.yaml must exist."""
        fpath = os.path.join(self.REPO_DIR, "examples", "mtls-demo", "deployments.yaml")
        assert os.path.isfile(fpath), "deployments.yaml not found"

    def test_service_yaml_exists(self):
        """examples/mtls-demo/service.yaml must exist."""
        fpath = os.path.join(self.REPO_DIR, "examples", "mtls-demo", "service.yaml")
        assert os.path.isfile(fpath), "service.yaml not found"

    def test_server_policy_exists(self):
        """examples/mtls-demo/server-policy.yaml must exist."""
        fpath = os.path.join(
            self.REPO_DIR, "examples", "mtls-demo", "server-policy.yaml"
        )
        assert os.path.isfile(fpath), "server-policy.yaml not found"

    def test_check_script_exists(self):
        """bin/check-mtls-demo.sh must exist."""
        fpath = os.path.join(self.REPO_DIR, "bin", "check-mtls-demo.sh")
        assert os.path.isfile(fpath), "check-mtls-demo.sh not found"

    # ------------------------------------------------------------------
    # L2: YAML content validation
    # ------------------------------------------------------------------

    def _load_all_yamls(self, relpath):
        """Load all YAML documents from a multi-doc file."""
        import yaml

        fpath = os.path.join(self.REPO_DIR, relpath)
        with open(fpath, "r") as f:
            return list(yaml.safe_load_all(f))

    def test_deployments_have_linkerd_inject(self):
        """Deployments must have linkerd.io/inject: enabled annotation."""
        docs = self._load_all_yamls("examples/mtls-demo/deployments.yaml")
        inject_count = 0
        for doc in docs:
            if doc and doc.get("kind") == "Deployment":
                annotations = (
                    doc.get("spec", {})
                    .get("template", {})
                    .get("metadata", {})
                    .get("annotations", {})
                )
                meta_annotations = doc.get("metadata", {}).get("annotations", {})
                all_annotations = {**meta_annotations, **annotations}
                if "linkerd.io/inject" in all_annotations:
                    inject_count += 1
        assert (
            inject_count >= 2
        ), f"Expected >= 2 deployments with linkerd.io/inject, found {inject_count}"

    def test_server_crd_defined(self):
        """server-policy.yaml must define a Server CRD."""
        docs = self._load_all_yamls("examples/mtls-demo/server-policy.yaml")
        server_found = any(d and d.get("kind") == "Server" for d in docs)
        assert server_found, "No Server CRD found in server-policy.yaml"

    def test_server_authorization_defined(self):
        """server-policy.yaml must define a ServerAuthorization CRD."""
        docs = self._load_all_yamls("examples/mtls-demo/server-policy.yaml")
        auth_found = any(d and d.get("kind") == "ServerAuthorization" for d in docs)
        assert auth_found, "No ServerAuthorization CRD found"

    def test_server_auth_requires_mtls(self):
        """ServerAuthorization must require mTLS identity."""
        docs = self._load_all_yamls("examples/mtls-demo/server-policy.yaml")
        for doc in docs:
            if doc and doc.get("kind") == "ServerAuthorization":
                content = str(doc)
                mtls_patterns = [
                    "meshTLS",
                    "identities",
                    "serviceAccount",
                    "meshTLS",
                    "authenticated",
                ]
                found = any(p in content for p in mtls_patterns)
                if found:
                    return
        pytest.fail("ServerAuthorization does not reference mTLS identity")

    def test_service_yaml_valid(self):
        """service.yaml must define a valid Service resource."""
        docs = self._load_all_yamls("examples/mtls-demo/service.yaml")
        svc_found = any(d and d.get("kind") == "Service" for d in docs)
        assert svc_found, "No Service resource found in service.yaml"

    def test_check_script_runs(self):
        """check-mtls-demo.sh must run with exit code 0."""
        result = subprocess.run(
            ["bash", "bin/check-mtls-demo.sh"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert (
            result.returncode == 0
        ), f"Check script failed:\n{result.stdout}\n{result.stderr}"

    def test_readme_exists(self):
        """examples/mtls-demo/README.md must exist."""
        fpath = os.path.join(self.REPO_DIR, "examples", "mtls-demo", "README.md")
        assert os.path.isfile(fpath), "README.md not found"
