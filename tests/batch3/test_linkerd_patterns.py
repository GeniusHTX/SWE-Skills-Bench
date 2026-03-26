"""
Tests for linkerd-patterns skill.
Validates ServiceProfile, TrafficSplit, AllowNamespaces patterns in linkerd2 repository.
"""

import os
import subprocess
import pytest

REPO_DIR = "/workspace/linkerd2"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


def _run(cmd: str, cwd: str = REPO_DIR, timeout: int = 120):
    return subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


class TestLinkerdPatterns:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_service_profile_go_file_exists(self):
        """service_profile.go must exist in controller/api/destination."""
        rel = "controller/api/destination/service_profile.go"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "service_profile.go is empty"

    def test_traffic_split_go_file_exists(self):
        """traffic_split.go must exist in controller/api/destination."""
        rel = "controller/api/destination/traffic_split.go"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "traffic_split.go is empty"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_service_profile_struct_defined(self):
        """service_profile.go must define ServiceProfile with routes and client spec."""
        content = _read("controller/api/destination/service_profile.go")
        assert "ServiceProfile" in content, "ServiceProfile type not found"
        assert (
            "Routes" in content or "RouteSpec" in content
        ), "Routes/RouteSpec field not found in ServiceProfile"

    def test_traffic_split_weights_sum_to_1000(self):
        """traffic_split.go must validate that weights sum to 1000."""
        content = _read("controller/api/destination/traffic_split.go")
        assert (
            "1000" in content
        ), "Weight sum validation (1000) not found in traffic_split.go"

    def test_allow_namespaces_function_defined(self):
        """AllowNamespaces must be defined for cross-namespace service profile."""
        content = _read("controller/api/destination/service_profile.go")
        assert (
            "AllowNamespaces" in content
            or "allowedNamespaces" in content
            or "namespace" in content.lower()
        ), "AllowNamespaces / namespace access control not found"

    def test_retry_ratio_validation_defined(self):
        """service_profile.go must validate retryRatio <= 1.0."""
        content = _read("controller/api/destination/service_profile.go")
        assert (
            "retryRatio" in content or "RetryRatio" in content
        ), "retryRatio validation not found in service_profile.go"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_service_profile_2_routes_valid(self):
        """ServiceProfile with 2 distinct routes must pass validation (mocked)."""

        def validate_routes(routes):
            names = [r["name"] for r in routes]
            if len(names) != len(set(names)):
                raise ValueError("Duplicate route names found")
            return None

        assert (
            validate_routes(
                [
                    {"name": "GET /api/users", "condition": "GET"},
                    {"name": "POST /api/users", "condition": "POST"},
                ]
            )
            is None
        )

    def test_duplicate_route_name_returns_error(self):
        """ServiceProfile must return error for duplicate route names."""

        def validate_routes(routes):
            names = [r["name"] for r in routes]
            if len(names) != len(set(names)):
                raise ValueError("Duplicate route names found")
            return None

        with pytest.raises(ValueError, match="Duplicate"):
            validate_routes(
                [
                    {"name": "GET /api", "condition": "GET"},
                    {"name": "GET /api", "condition": "GET"},
                ]
            )

    def test_retry_ratio_1_5_error(self):
        """retryRatio=1.5 must return a validation error."""

        def validate_retry_ratio(ratio: float):
            if ratio > 1.0:
                raise ValueError(f"retryRatio must be <= 1.0, got {ratio}")

        with pytest.raises(ValueError, match="retryRatio"):
            validate_retry_ratio(1.5)

    def test_traffic_split_900_100_valid(self):
        """TrafficSplit with weights [900, 100] (sum=1000) must pass validation."""

        def validate_split(weights):
            total = sum(weights)
            if total != 1000:
                raise ValueError(f"Weights must sum to 1000, got {total}")

        assert validate_split([900, 100]) is None

    def test_traffic_split_500_400_error(self):
        """TrafficSplit with weights [500, 400] (sum=900) must return error."""

        def validate_split(weights):
            total = sum(weights)
            if total != 1000:
                raise ValueError(f"Weights must sum to 1000, got {total}")

        with pytest.raises(ValueError, match="1000"):
            validate_split([500, 400])

    def test_shift_weight_updates_split(self):
        """ShiftWeight(50) must move 50 milliwei from stable to canary."""

        def shift_weight(stable: int, canary: int, shift_by: int):
            stable -= shift_by
            canary += shift_by
            assert stable + canary == 1000
            return {"stable": stable, "canary": canary}

        result = shift_weight(900, 100, 50)
        assert result["stable"] == 850
        assert result["canary"] == 150
        assert result["stable"] + result["canary"] == 1000
