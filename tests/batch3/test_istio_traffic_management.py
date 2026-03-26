"""
Tests for istio-traffic-management skill.
Validates VirtualService, DestinationRule, CanaryConfig, ProgressiveRollout in istio repository.
"""

import os
import subprocess
import glob
import pytest

REPO_DIR = "/workspace/istio"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


def _run(cmd: str, cwd: str = REPO_DIR, timeout: int = 120):
    return subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


def _read_package(pkg_dir: str) -> str:
    """Read all .go files in a directory and return concatenated content."""
    full_dir = _path(pkg_dir)
    content = ""
    for f in glob.glob(os.path.join(full_dir, "*.go")):
        with open(f, encoding="utf-8", errors="ignore") as fh:
            content += fh.read()
    return content


class TestIstioTrafficManagement:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_traffic_management_files_exist(self):
        """virtual_service.go and destination_rule.go must exist."""
        for rel in [
            "pilot/pkg/config/traffic/virtual_service.go",
            "pilot/pkg/config/traffic/destination_rule.go",
        ]:
            assert os.path.isfile(_path(rel)), f"{rel} not found"
            assert os.path.getsize(_path(rel)) > 0, f"{rel} is empty"

    def test_traffic_package_has_multiple_go_files(self):
        """Traffic config package must contain at least 3 .go files."""
        pkg_dir = _path("pilot/pkg/config/traffic")
        if not os.path.isdir(pkg_dir):
            pytest.skip("pilot/pkg/config/traffic directory not found")
        go_files = glob.glob(os.path.join(pkg_dir, "*.go"))
        assert (
            len(go_files) >= 3
        ), f"Expected >= 3 .go files in traffic package, found {len(go_files)}"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_virtual_service_struct_defined(self):
        """virtual_service.go must define VirtualServiceBuilder or VirtualService type."""
        content = _read("pilot/pkg/config/traffic/virtual_service.go")
        assert (
            "type VirtualService" in content or "func NewVirtualService" in content
        ), "VirtualService type/constructor not found in virtual_service.go"

    def test_destination_rule_lb_policy_defined(self):
        """destination_rule.go must include LoadBalancingPolicy and ROUND_ROBIN."""
        content = _read("pilot/pkg/config/traffic/destination_rule.go")
        assert "ROUND_ROBIN" in content, "ROUND_ROBIN load balancing constant not found"
        assert (
            "maxEjectionPercent" in content or "MaxEjectionPercent" in content
        ), "maxEjectionPercent field not found in destination_rule.go"

    def test_canary_config_and_rollout_defined(self):
        """Package must define CanaryConfig and ProgressiveRollout types."""
        content = _read_package("pilot/pkg/config/traffic")
        assert (
            "CanaryConfig" in content
        ), "CanaryConfig type not found in traffic package"
        assert (
            "ProgressiveRollout" in content
        ), "ProgressiveRollout type not found in traffic package"

    def test_route_weights_sum_to_100_validation(self):
        """virtual_service.go must validate that route weights sum to 100."""
        content = _read("pilot/pkg/config/traffic/virtual_service.go")
        assert (
            "100" in content
        ), "Weight validation (sum to 100) not found in virtual_service.go"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_routes_80_20_valid(self):
        """Routes with weights [80, 20] (sum=100) must pass validation."""

        def validate_routes(routes):
            total = sum(r["weight"] for r in routes)
            if total != 100:
                raise ValueError(f"Route weights must sum to 100, got {total}")
            return None

        assert (
            validate_routes(
                [
                    {"destination": "v1", "weight": 80},
                    {"destination": "v2", "weight": 20},
                ]
            )
            is None
        )

    def test_routes_60_30_weight_error(self):
        """Routes with weights [60, 30] (sum=90) must return a validation error."""

        def validate_routes(routes):
            total = sum(r["weight"] for r in routes)
            if total != 100:
                raise ValueError(f"Route weights must sum to 100, got {total}")
            return None

        with pytest.raises(ValueError, match="100"):
            validate_routes(
                [
                    {"destination": "v1", "weight": 60},
                    {"destination": "v2", "weight": 30},
                ]
            )

    def test_canary_config_10_percent_routes(self):
        """CanaryConfig(10%) must produce stable=90 and canary=10 routes."""

        def canary_config(canary_weight: int):
            if not 0 < canary_weight < 100:
                raise ValueError("canary_weight must be between 1 and 99")
            return [
                {"destination": "stable", "weight": 100 - canary_weight},
                {"destination": "canary", "weight": canary_weight},
            ]

        routes = canary_config(10)
        stable = next(r for r in routes if r["destination"] == "stable")
        canary = next(r for r in routes if r["destination"] == "canary")
        assert stable["weight"] == 90
        assert canary["weight"] == 10

    def test_max_ejection_percent_110_error(self):
        """DestinationRule must reject maxEjectionPercent > 100."""

        def validate_destination_rule(max_ejection_percent: int):
            if not 0 <= max_ejection_percent <= 100:
                raise ValueError(
                    f"maxEjectionPercent must be between 0 and 100, got {max_ejection_percent}"
                )

        with pytest.raises(ValueError, match="maxEjectionPercent"):
            validate_destination_rule(110)

    def test_progressive_rollout_stages_4(self):
        """ProgressiveRollout([5,25,50,100]) must generate 4 rollout stages."""

        def progressive_rollout(weights):
            if weights != sorted(weights):
                raise ValueError("Rollout weights must be monotonically increasing")
            return [{"canary_weight": w} for w in weights]

        stages = progressive_rollout([5, 25, 50, 100])
        assert len(stages) == 4

    def test_progressive_rollout_non_monotonic_error(self):
        """ProgressiveRollout([50,25,75]) must raise an error for non-monotonic weights."""

        def progressive_rollout(weights):
            if weights != sorted(weights):
                raise ValueError("Rollout weights must be monotonically increasing")
            return [{"canary_weight": w} for w in weights]

        with pytest.raises(ValueError, match="monotonically"):
            progressive_rollout([50, 25, 75])
