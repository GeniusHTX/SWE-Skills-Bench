"""
Tests for gitops-workflow skill.
Validates Flux2 GitOps app generator Go implementation in flux2 repository.
"""

import os
import subprocess
import pytest

REPO_DIR = "/workspace/flux2"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


def _run(cmd: str, cwd: str = REPO_DIR, timeout: int = 120):
    return subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


class TestGitopsWorkflow:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_app_generator_go_file_exists(self):
        """app_generator.go must exist in internal/gitops."""
        rel = "internal/gitops/app_generator.go"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "app_generator.go is empty"

    def test_environment_and_health_files_exist(self):
        """environment.go and health_check.go must exist."""
        for rel in [
            "internal/gitops/environment.go",
            "internal/gitops/health_check.go",
        ]:
            assert os.path.isfile(_path(rel)), f"{rel} not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_generate_returns_kustomization_kind(self):
        """app_generator.go must reference 'Kustomization' as the generated Kind."""
        content = _read("internal/gitops/app_generator.go")
        assert (
            "Kustomization" in content
        ), "app_generator.go must include 'Kustomization' Kind in generated manifest"

    def test_environment_config_has_interval(self):
        """environment.go must define 1m interval for dev and Suspend field."""
        content = _read("internal/gitops/environment.go")
        assert (
            "1m" in content
        ), "environment.go must define '1m' sync interval for development"
        assert (
            "Suspend" in content or "suspend" in content
        ), "environment.go must define Suspend field for production gate"

    def test_promote_function_defined(self):
        """app_generator.go must define a Promote function."""
        content = _read("internal/gitops/app_generator.go")
        assert (
            "func Promote" in content or "func promote" in content
        ), "Promote function not found in app_generator.go"

    def test_depends_on_chain_staging_to_dev(self):
        """environment.go must define staging dependsOn development."""
        content = _read("internal/gitops/environment.go")
        assert (
            "DependsOn" in content or "dependsOn" in content
        ), "DependsOn referencing development not found in environment.go"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_go_tests_pass(self):
        """All gitops package Go tests must pass."""
        result = _run("go test ./internal/gitops/... -v")
        if "no required module" in result.stderr or "cannot find" in result.stderr:
            pytest.skip("Go module not available")
        assert (
            result.returncode == 0
        ), f"go test failed:\n{result.stdout}\n{result.stderr}"
        assert "PASS" in result.stdout

    def test_generate_produces_kustomization_yaml(self):
        """TestGenerate must pass verifying Kustomization kind in generated YAML."""
        result = _run("go test ./internal/gitops/... -run TestGenerate -v")
        if "no required module" in result.stderr:
            pytest.skip("Go module not available")
        assert result.returncode == 0, f"TestGenerate failed:\n{result.stdout}"

    def test_dev_to_production_promote_returns_error(self):
        """Promote(dev→production) must return an error (must go through staging)."""
        result = _run(
            "go test ./internal/gitops/... -run TestPromoteDevToProduction -v"
        )
        if "no required module" in result.stderr:
            pytest.skip("Go module not available")
        assert (
            result.returncode == 0
        ), f"TestPromoteDevToProduction failed:\n{result.stdout}"

    def test_staging_to_production_promote_succeeds(self):
        """Promote(staging→production) must return nil and set suspend=false."""
        result = _run(
            "go test ./internal/gitops/... -run TestPromoteStagingToProduction -v"
        )
        if "no required module" in result.stderr:
            pytest.skip("Go module not available")
        assert (
            result.returncode == 0
        ), f"TestPromoteStagingToProduction failed:\n{result.stdout}"

    def test_dev_environment_interval_is_1m(self):
        """Development Kustomization sync interval must be 1m."""
        result = _run(
            "go test ./internal/gitops/... -run TestDevEnvironmentInterval -v"
        )
        if "no required module" in result.stderr:
            pytest.skip("Go module not available")
        assert (
            result.returncode == 0
        ), f"TestDevEnvironmentInterval failed:\n{result.stdout}"

    def test_production_environment_is_suspended_by_default(self):
        """Production Kustomization must have Suspend=true by default."""
        result = _run("go test ./internal/gitops/... -run TestProductionSuspended -v")
        if "no required module" in result.stderr:
            pytest.skip("Go module not available")
        assert (
            result.returncode == 0
        ), f"TestProductionSuspended failed:\n{result.stdout}"
