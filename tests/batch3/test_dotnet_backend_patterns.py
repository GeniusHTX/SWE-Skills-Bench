"""
Tests for dotnet-backend-patterns skill.
Validates .NET Catalog API async patterns, EF projections, caching, and pagination.
"""

import os
import subprocess
import re
import pytest

REPO_DIR = "/workspace/dotnet-backend-patterns"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


def _run(cmd: str, cwd: str = REPO_DIR, timeout: int = 120):
    return subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


class TestDotnetBackendPatterns:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_catalog_service_file_exists(self):
        """CatalogService.cs must exist in Services directory."""
        rel = "src/Catalog.API/Services/CatalogService.cs"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "CatalogService.cs is empty"

    def test_catalog_api_file_exists(self):
        """CatalogApi.cs must exist in Apis directory."""
        rel = "src/Catalog.API/Apis/CatalogApi.cs"
        assert os.path.isfile(_path(rel)), f"{rel} not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_no_sync_blocking_calls(self):
        """CatalogService.cs must not use .Result or .Wait() blocking patterns."""
        content = _read("src/Catalog.API/Services/CatalogService.cs")
        assert (
            ".Result" not in content
        ), "CatalogService.cs must not use .Result (deadlock risk)"
        assert (
            ".Wait()" not in content
        ), "CatalogService.cs must not use .Wait() (deadlock risk)"

    def test_select_projections_present(self):
        """CatalogService.cs must use .Select() LINQ projections for DTOs."""
        content = _read("src/Catalog.API/Services/CatalogService.cs")
        assert (
            ".Select(" in content
        ), "CatalogService.cs must use .Select() for DTO projections"

    def test_caching_interface_referenced(self):
        """CatalogService.cs must reference IMemoryCache or IDistributedCache."""
        content = _read("src/Catalog.API/Services/CatalogService.cs")
        assert (
            "IMemoryCache" in content or "IDistributedCache" in content
        ), "CatalogService.cs must inject caching interface"

    def test_pagination_uses_skip_take(self):
        """CatalogService.cs must use .Skip() and .Take() for pagination."""
        content = _read("src/Catalog.API/Services/CatalogService.cs")
        assert ".Skip(" in content, "CatalogService.cs must use .Skip() for pagination"
        assert ".Take(" in content, "CatalogService.cs must use .Take() for pagination"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_dotnet_build_succeeds(self):
        """Catalog.API project must build without compilation errors."""
        result = _run("dotnet build src/Catalog.API/ --no-restore")
        if (
            "command not found" in result.stderr.lower()
            or "is not recognized" in result.stderr
        ):
            pytest.skip("dotnet CLI not available")
        assert (
            result.returncode == 0
        ), f"Build failed:\n{result.stdout}\n{result.stderr}"
        assert "Build succeeded" in result.stdout

    def test_all_service_methods_are_async(self):
        """All public service methods in CatalogService.cs must return Task or Task<T>."""
        content = _read("src/Catalog.API/Services/CatalogService.cs")
        # Find public methods that are NOT async and NOT constructors
        public_methods = re.findall(r"public\s+(\S+)\s+\w+\s*\(", content)
        non_async = [
            m
            for m in public_methods
            if m not in ("async", "CatalogService", "override") and "Task" not in m
        ]
        assert (
            len(non_async) == 0
        ), f"Non-async public methods found with return types: {non_async}"

    def test_api_returns_not_found_for_missing_resources(self):
        """CatalogApi.cs must return TypedResults.NotFound or Problem() for 404s."""
        content = _read("src/Catalog.API/Apis/CatalogApi.cs")
        assert (
            "TypedResults.NotFound" in content or "Problem(" in content
        ), "CatalogApi.cs must return proper 404 responses"

    def test_catalog_api_endpoint_registration(self):
        """CatalogApi.cs must register endpoints using MapGet/MapPost/MapDelete."""
        content = _read("src/Catalog.API/Apis/CatalogApi.cs")
        assert any(
            kw in content for kw in ["MapGet", "MapPost", "MapDelete", "MapPut"]
        ), "CatalogApi.cs must use Minimal API route registration"

    def test_service_constructor_injects_dependencies(self):
        """CatalogService constructor must accept dependency injection parameters."""
        content = _read("src/Catalog.API/Services/CatalogService.cs")
        ctor_match = re.search(r"public\s+CatalogService\s*\(([^)]+)\)", content)
        assert ctor_match is not None, "CatalogService constructor not found"
        assert (
            len(ctor_match.group(1).strip()) > 0
        ), "CatalogService constructor must accept at least one dependency"

    def test_service_does_not_use_magic_strings_for_cache_keys(self):
        """Cache keys in CatalogService.cs must not be bare magic strings."""
        content = _read("src/Catalog.API/Services/CatalogService.cs")
        has_const = "const string" in content or "nameof(" in content or '$"' in content
        assert (
            has_const
        ), "CatalogService.cs should use constants or string interpolation for cache keys"
