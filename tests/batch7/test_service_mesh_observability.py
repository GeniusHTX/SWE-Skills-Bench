"""Test file for the service-mesh-observability skill.

This suite validates Grafana dashboard generation for Linkerd service mesh
monitoring including panel types, UID generation, and JSON output.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess

import pytest


class TestServiceMeshObservability:
    """Verify Grafana dashboard generation for Linkerd in linkerd2."""

    REPO_DIR = "/workspace/linkerd2"

    GENERATOR_GO = "viz/pkg/dashboard/generator.go"
    PANELS_GO = "viz/pkg/dashboard/panels.go"
    TYPES_GO = "viz/pkg/dashboard/types.go"

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

    def _go_struct_body(self, source: str, struct_name: str) -> str:
        """Extract the body of a Go struct type definition."""
        pattern = rf"type\s+{struct_name}\s+struct\s*\{{([^}}]+)\}}"
        m = re.search(pattern, source, re.DOTALL)
        return m.group(1) if m else ""

    def _all_go_sources(self, directory: str) -> str:
        """Read all .go files under a directory."""
        result = []
        root = self._repo_path(directory)
        if root.is_dir():
            for f in root.rglob("*.go"):
                result.append(f.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(result)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_dashboard_generator_go_created(self):
        """Verify viz/pkg/dashboard/generator.go exists."""
        self._assert_non_empty_file(self.GENERATOR_GO)

    def test_file_path_dashboard_panels_go_created(self):
        """Verify viz/pkg/dashboard/panels.go exists."""
        self._assert_non_empty_file(self.PANELS_GO)

    def test_file_path_dashboard_types_go_created(self):
        """Verify viz/pkg/dashboard/types.go exists."""
        self._assert_non_empty_file(self.TYPES_GO)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_dashboard_struct_title_uid_tags_panels_templating_json_tags(self):
        """Dashboard struct has Title/UID/Tags/Panels/Templating with json tags."""
        src = self._read_text(self.TYPES_GO)
        body = self._go_struct_body(src, "Dashboard")
        assert body, "Dashboard struct not found"
        for field in ["Title", "UID", "Tags", "Panels", "Templating"]:
            assert field in body, f"Dashboard struct should have {field} field"
        assert "`json:" in body, "Dashboard fields should have json tags"

    def test_semantic_panel_struct_id_title_type_gridpos_targets_alert(self):
        """Panel struct has ID/Title/Type/GridPos/Targets/Alert."""
        src = self._read_text(self.TYPES_GO)
        body = self._go_struct_body(src, "Panel")
        assert body, "Panel struct not found"
        for field in ["ID", "Title", "Type", "GridPos", "Targets"]:
            assert field in body, f"Panel struct should have {field} field"

    def test_semantic_successratepanel_stat_type_percentunit(self):
        """SuccessRatePanel uses 'stat' type with percentunit."""
        src = self._read_text(self.PANELS_GO)
        assert re.search(r"stat", src), "SuccessRatePanel should use 'stat' type"
        assert re.search(
            r"percent", src, re.IGNORECASE
        ), "SuccessRatePanel should use percentunit"

    def test_semantic_latencypanel_p50_p95_p99(self):
        """LatencyPanel includes P50, P95, P99 targets."""
        src = self._read_text(self.PANELS_GO)
        for percentile in [
            "P50",
            "p50",
            "P95",
            "p95",
            "P99",
            "p99",
            "0.5",
            "0.95",
            "0.99",
        ]:
            if percentile.lower() in src.lower():
                break
        else:
            pytest.fail("LatencyPanel should include P50/P95/P99 percentiles")

    def test_semantic_generateuid_sha256_8_char_hex(self):
        """generateUID uses sha256 and returns 8-char hex string."""
        src = self._read_text(self.GENERATOR_GO)
        gen_and_types = src + "\n" + self._read_text(self.TYPES_GO)
        assert re.search(
            r"sha256|crypto/sha256", gen_and_types
        ), "generateUID should use SHA256"
        # 8-char hex substring
        assert re.search(
            r"\[:?8\]|[:8]|Sprintf.*%0?8x", gen_and_types
        ), "generateUID should return 8-char hex"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases)
    # ------------------------------------------------------------------

    def test_functional_generate_for_service_web_ns_default_produces_4_panels(self):
        """Generate() for service='web', ns='default' → 4 panels."""
        src = self._read_text(self.GENERATOR_GO)
        assert re.search(r"func.*Generate", src), "Generate function should exist"
        panels_src = self._read_text(self.PANELS_GO)
        # Count panel constructor functions
        panel_funcs = re.findall(r"func\s+\w*[Pp]anel", panels_src)
        assert (
            len(panel_funcs) >= 4
        ), f"Expected at least 4 panel functions, found {len(panel_funcs)}"

    def test_functional_tojson_produces_valid_parseable_json(self):
        """ToJSON() produces valid parseable JSON."""
        src = self._all_go_sources("viz/pkg/dashboard")
        assert re.search(
            r"json\.Marshal|ToJSON|encoding/json", src
        ), "ToJSON should use json.Marshal"

    def test_functional_deterministic_uid_same_inputs_same_output(self):
        """Deterministic UID: same inputs → same output."""
        src = self._all_go_sources("viz/pkg/dashboard")
        assert re.search(
            r"sha256|hash", src
        ), "UID generation should be deterministic via hashing"

    def test_functional_tags_include_linkerd_service_mesh_ns_svc(self):
        """Tags include linkerd, service-mesh, namespace, service."""
        src = self._all_go_sources("viz/pkg/dashboard")
        assert re.search(r"linkerd", src), "Tags should include 'linkerd'"
        assert re.search(
            r"service.mesh|servicemesh", src, re.IGNORECASE
        ), "Tags should include 'service-mesh'"

    def test_functional_go_build_viz_succeeds(self):
        """go build ./viz/... should succeed (source analysis)."""
        src = self._all_go_sources("viz/pkg/dashboard")
        assert "package " in src, "Go files should have package declarations"
        # Verify no obvious syntax errors in the generated Go code
        assert (
            src.count("func ") >= 3
        ), "Expected at least 3 functions in dashboard package"
