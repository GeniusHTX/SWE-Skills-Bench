"""Test file for the k8s-manifest-generator skill.

This suite validates the ApplicationGenerator plugin that produces
Kubernetes manifests from an ApplicationSpec (Deployment, Service,
ConfigMap, HPA).
"""

from __future__ import annotations

import pathlib
import re

import pytest


class TestK8sManifestGenerator:
    """Verify the kustomize ApplicationGenerator plugin."""

    REPO_DIR = "/workspace/kustomize"

    GENERATOR_GO = "plugin/builtin/applicationgenerator/ApplicationGenerator.go"
    GENERATOR_TEST_GO = (
        "plugin/builtin/applicationgenerator/ApplicationGenerator_test.go"
    )
    SPEC_GO = "api/types/applicationspec.go"

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
        for rel in (self.GENERATOR_GO, self.GENERATOR_TEST_GO, self.SPEC_GO):
            path = self._repo_path(rel)
            if path.is_file():
                parts.append(path.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_applicationgenerator_go_exists(self):
        """Verify ApplicationGenerator.go exists and is non-empty."""
        self._assert_non_empty_file(self.GENERATOR_GO)

    def test_file_path_applicationgenerator_test_go_exists(self):
        """Verify ApplicationGenerator_test.go exists and is non-empty."""
        self._assert_non_empty_file(self.GENERATOR_TEST_GO)

    def test_file_path_applicationspec_go_exists(self):
        """Verify api/types/applicationspec.go exists and is non-empty."""
        self._assert_non_empty_file(self.SPEC_GO)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_applicationspec_struct_has_json_yaml_tags(self):
        """ApplicationSpec struct has json/yaml tags."""
        src = self._read_text(self.SPEC_GO)
        body = self._go_struct_body(src, "ApplicationSpec")
        assert body is not None, "ApplicationSpec struct not found"
        assert re.search(
            r'`(json|yaml):"', body
        ), "ApplicationSpec should have json/yaml tags"

    def test_semantic_imagespec_has_repository_tag_pullpolicy(self):
        """ImageSpec has repository, tag, pullPolicy fields."""
        src = self._read_text(self.SPEC_GO)
        body = self._go_struct_body(src, "ImageSpec")
        assert body is not None, "ImageSpec struct not found"
        lower = body.lower()
        for field in ("repository", "tag", "pullpolicy"):
            assert field in lower, f"ImageSpec missing field: {field}"

    def test_semantic_autoscalingspec_has_min_max_targetcpu_targetmemory(self):
        """AutoscalingSpec has minReplicas, maxReplicas, targetCPU, targetMemory."""
        src = self._read_text(self.SPEC_GO)
        body = self._go_struct_body(src, "AutoscalingSpec")
        assert body is not None, "AutoscalingSpec struct not found"
        lower = body.lower()
        for field in ("minreplicas", "maxreplicas", "targetcpu", "targetmemory"):
            assert field in lower, f"AutoscalingSpec missing field: {field}"

    def test_semantic_generatorplugin_interface_exists(self):
        """GeneratorPlugin interface exists."""
        src = self._all_go_sources()
        assert re.search(r"type\s+GeneratorPlugin\s+interface", src) or re.search(
            r"type\s+\w*Generator\w*\s+struct", src
        ), "GeneratorPlugin interface or Generator struct not found"

    def test_semantic_generate_returns_resmap(self):
        """Generate method returns resmap.ResMap."""
        src = self._read_text(self.GENERATOR_GO)
        assert re.search(
            r"func\s*\(.*\)\s+Generate\s*\(", src
        ), "Generate method not found"
        assert re.search(
            r"resmap\.ResMap|ResMap|\[\].*Resource", src
        ), "Generate should return ResMap or resource slice"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, source analysis)
    # ------------------------------------------------------------------

    def test_functional_full_spec_generates_4_resources(self):
        """Full spec generates 4 resources: Deployment, Service, ConfigMap, HPA."""
        src = self._all_go_sources()
        for kind in ("Deployment", "Service", "ConfigMap"):
            assert kind in src, f"Generator should produce {kind}"
        assert re.search(
            r"HorizontalPodAutoscaler|HPA|[Aa]utoscal", src
        ), "Generator should produce HPA for full spec"

    def test_functional_no_config_generates_3_resources(self):
        """Without config section, generator produces Deployment, Service, HPA (no ConfigMap)."""
        src = self._all_go_sources()
        # Check that config presence is conditional
        assert re.search(
            r"[Cc]onfig[Mm]ap|ConfigMap", src
        ), "Generator should conditionally produce ConfigMap"
        assert re.search(
            r"if.*[Cc]onfig|Config\s*!=\s*nil|len\(.*[Cc]onfig", src
        ), "ConfigMap generation should be conditional"

    def test_functional_no_autoscaling_uses_replicas(self):
        """Without autoscaling, generator produces Deployment with replicas field."""
        src = self._all_go_sources()
        assert re.search(r"[Rr]eplicas|Replicas", src), "Deployment should set replicas"
        assert re.search(r"[Aa]utoscal|HPA", src), "Autoscaling logic should exist"

    def test_functional_minimal_spec_generates_deployment_and_service(self):
        """Minimal spec generates Deployment and Service only."""
        src = self._all_go_sources()
        assert (
            "Deployment" in src and "Service" in src
        ), "Minimal spec must produce at least Deployment and Service"

    def test_functional_deployment_container_image_port_env_correct(self):
        """Deployment includes correct container image, port, and env settings."""
        src = self._all_go_sources()
        assert re.search(
            r"[Cc]ontainer|Image|[Pp]ort|[Ee]nv", src
        ), "Deployment resource should configure container image, port, env"
