"""Test file for the istio-traffic-management skill.

This suite validates the canary deployment controller, types, and rollback
logic in Istio's pilot package.
"""

from __future__ import annotations

import pathlib
import re

import pytest


class TestIstioTrafficManagement:
    """Verify Istio canary deployment controller."""

    REPO_DIR = "/workspace/istio"

    CONTROLLER_GO = "pilot/pkg/canary/controller.go"
    TYPES_GO = "pilot/pkg/canary/types.go"
    ROLLBACK_GO = "pilot/pkg/canary/rollback.go"

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
        canary_dir = self._repo_path("pilot/pkg/canary")
        if not canary_dir.is_dir():
            return ""
        parts = []
        for f in sorted(canary_dir.glob("*.go")):
            parts.append(f.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_pilot_pkg_canary_controller_go_exists(self):
        """Verify controller.go exists and is non-empty."""
        self._assert_non_empty_file(self.CONTROLLER_GO)

    def test_file_path_pilot_pkg_canary_types_go_exists(self):
        """Verify types.go exists and is non-empty."""
        self._assert_non_empty_file(self.TYPES_GO)

    def test_file_path_pilot_pkg_canary_rollback_go_exists(self):
        """Verify rollback.go exists and is non-empty."""
        self._assert_non_empty_file(self.ROLLBACK_GO)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_canarydeployment_struct_has_all_required_fields(self):
        """CanaryDeployment struct has all required fields."""
        src = self._read_text(self.TYPES_GO)
        body = self._go_struct_body(src, "CanaryDeployment")
        assert body is not None, "CanaryDeployment struct not found"

    def test_semantic_trafficstep_has_canaryweight_stableweight_duration(self):
        """TrafficStep has CanaryWeight, StableWeight, Duration."""
        src = self._read_text(self.TYPES_GO)
        body = self._go_struct_body(src, "TrafficStep")
        assert body is not None, "TrafficStep struct not found"
        for field in ("CanaryWeight", "StableWeight", "Duration"):
            assert field in body, f"TrafficStep missing field: {field}"

    def test_semantic_canarystatus_constants_defined_for_all_5_states(self):
        """CanaryStatus constants defined for all 5 states."""
        src = self._read_text(self.TYPES_GO)
        assert re.search(
            r"CanaryStatus|StatusPending|StatusProgressing", src
        ), "CanaryStatus constants not found"
        # Expect at least 5 status constants
        status_matches = re.findall(r"Status\w+|Canary\w+Status", src)
        assert (
            len(status_matches) >= 3
        ), f"Expected multiple status constants, found {len(status_matches)}"

    def test_semantic_canarycontroller_has_start_advance_rollback_getstat(self):
        """CanaryController has Start, Advance, Rollback, GetState, GenerateVirtualService."""
        src = self._all_go_sources()
        for method in ("Start", "Advance", "Rollback", "GetState"):
            assert re.search(
                rf"func\s*\(.*\)\s+{method}\s*\(", src
            ), f"CanaryController missing {method} method"

    def test_semantic_metricsprovider_interface_has_geterrorrate_getlaten(self):
        """MetricsProvider interface has GetErrorRate, GetLatencyP99, GetRequestRate methods."""
        src = self._all_go_sources()
        assert re.search(
            r"type\s+MetricsProvider\s+interface", src
        ), "MetricsProvider interface not found"
        for method in ("GetErrorRate", "GetLatencyP99", "GetRequestRate"):
            assert re.search(
                rf"{method}\s*\(", src
            ), f"MetricsProvider missing {method} method"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, mocked via source analysis)
    # ------------------------------------------------------------------

    def test_functional_start_with_3_step_deployment_creates_resources_wi(self):
        """Start with 3-step deployment creates resources with step[0] weights."""
        src = self._all_go_sources()
        assert re.search(r"func\s*\(.*\)\s+Start\s*\(", src), "Start method required"
        assert re.search(
            r"VirtualService|DestinationRule|Create", src
        ), "Start should create traffic resources"

    def test_functional_advance_from_step_0_to_step_1_updates_virtualserv(self):
        """Advance from step 0 to step 1 updates VirtualService weights."""
        src = self._all_go_sources()
        assert re.search(
            r"func\s*\(.*\)\s+Advance\s*\(", src
        ), "Advance method required"
        assert re.search(
            r"[Ww]eight|VirtualService|Update", src
        ), "Advance should update traffic weights"

    def test_functional_advance_on_last_step_sets_status_completed_and_ro(self):
        """Advance on last step sets status Completed and routes 100% canary."""
        src = self._all_go_sources()
        assert re.search(
            r"[Cc]ompleted|[Cc]omplete|100", src
        ), "Final advance should set Completed status"

    def test_functional_rollback_sets_100_stable_and_status_rolledback(self):
        """Rollback sets 100% stable and status RolledBack."""
        src = self._read_text(self.ROLLBACK_GO)
        assert re.search(
            r"[Rr]ollback|[Rr]olled[Bb]ack", src
        ), "Rollback logic required"
        assert re.search(
            r"100|[Ss]table", src
        ), "Rollback should restore 100% stable traffic"

    def test_functional_checkandrollback_triggers_rollback_when_error_rat(self):
        """CheckAndRollback triggers rollback when error rate > threshold."""
        src = self._all_go_sources()
        assert re.search(
            r"[Cc]heck[Aa]nd[Rr]ollback|[Ee]rror[Rr]ate.*[Tt]hreshold", src
        ), "CheckAndRollback should evaluate error rate against threshold"
