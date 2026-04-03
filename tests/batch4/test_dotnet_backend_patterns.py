"""
Test for 'dotnet-backend-patterns' skill — Catalog Service Optimization
Validates that the Agent optimized the eShop Catalog API with async patterns,
DTO projections, caching, and concurrent data access improvements.
"""

import os
import re

import pytest


class TestDotnetBackendPatterns:
    """Verify eShop Catalog API optimization."""

    REPO_DIR = "/workspace/eshop"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    # ---- file_path_check ----

    def test_catalog_service_file_exists(self):
        """Proves that CatalogService.cs exists at its declared path."""
        path = os.path.join(self.REPO_DIR, "src/Catalog.API/Services/CatalogService.cs")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_catalog_api_file_exists(self):
        """Proves that CatalogApi.cs exists at its declared endpoint layer path."""
        path = os.path.join(self.REPO_DIR, "src/Catalog.API/Apis/CatalogApi.cs")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_catalog_context_file_exists(self):
        """Proves that CatalogContext.cs exists at its declared infrastructure path."""
        path = os.path.join(
            self.REPO_DIR, "src/Catalog.API/Infrastructure/CatalogContext.cs"
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    # ---- semantic_check ----

    def test_catalog_service_async_await_task_present(self):
        """Proves CatalogService.cs uses async/await with Task<T> return types."""
        path = os.path.join(self.REPO_DIR, "src/Catalog.API/Services/CatalogService.cs")
        content = self._read(path)
        assert "async" in content, "Missing 'async' keyword in CatalogService.cs"
        assert "await" in content, "Missing 'await' keyword in CatalogService.cs"
        assert "Task<" in content, "Missing 'Task<' return type in CatalogService.cs"

    def test_catalog_service_no_sync_over_async(self):
        """Detects sync-over-async anti-pattern (.Result / .Wait()) in CatalogService.cs."""
        path = os.path.join(self.REPO_DIR, "src/Catalog.API/Services/CatalogService.cs")
        content = self._read(path)
        matches = re.findall(r"\.Result\b|\.Wait\(", content)
        assert (
            matches == []
        ), f"Sync-over-async anti-pattern found in CatalogService.cs: {matches}"

    def test_catalog_service_cache_interface_declared(self):
        """Proves CatalogService.cs declares a dependency on a cache interface."""
        path = os.path.join(self.REPO_DIR, "src/Catalog.API/Services/CatalogService.cs")
        content = self._read(path)
        alternatives = ["IMemoryCache", "IDistributedCache", "MemoryCache"]
        found = [a for a in alternatives if a in content]
        assert found, (
            f"No cache interface found in CatalogService.cs. "
            f"Expected one of {alternatives}"
        )

    def test_catalog_api_endpoints_are_async(self):
        """Proves CatalogApi.cs endpoint handlers use async."""
        path = os.path.join(self.REPO_DIR, "src/Catalog.API/Apis/CatalogApi.cs")
        content = self._read(path)
        assert "async" in content, "CatalogApi.cs endpoints are not async"

    def test_catalog_context_has_query_optimization_indicators(self):
        """Proves CatalogContext.cs has query optimization indicators (Select/Skip/projection)."""
        path = os.path.join(
            self.REPO_DIR, "src/Catalog.API/Infrastructure/CatalogContext.cs"
        )
        content = self._read(path)
        lower = content.lower()
        found = (
            "Select(" in content
            or ".Select(" in content
            or "Skip" in content
            or "projection" in lower
        )
        assert found, (
            "No query optimization indicators found in CatalogContext.cs "
            "(expected Select(, Skip, or 'projection')"
        )

    # ---- functional_check ----

    def test_catalog_api_no_sync_over_async(self):
        """Detects sync-over-async regression in CatalogApi.cs endpoint layer."""
        path = os.path.join(self.REPO_DIR, "src/Catalog.API/Apis/CatalogApi.cs")
        content = self._read(path)
        matches = re.findall(r"\.Result\b|\.Wait\(", content)
        assert (
            matches == []
        ), f"Sync-over-async anti-pattern found in CatalogApi.cs: {matches}"

    def test_catalog_context_skip_present_for_pagination(self):
        """Proves CatalogContext.cs uses Skip() for offset-based pagination."""
        path = os.path.join(
            self.REPO_DIR, "src/Catalog.API/Infrastructure/CatalogContext.cs"
        )
        content = self._read(path)
        assert (
            "Skip(" in content
        ), "Missing Skip() call — pagination not implemented in CatalogContext.cs"

    def test_catalog_context_take_present_for_pagination(self):
        """Proves CatalogContext.cs uses Take() to limit rows returned."""
        path = os.path.join(
            self.REPO_DIR, "src/Catalog.API/Infrastructure/CatalogContext.cs"
        )
        content = self._read(path)
        assert (
            "Take(" in content
        ), "Missing Take() call — unbounded result sets in CatalogContext.cs"

    def test_catalog_context_count_query_for_pagination_total(self):
        """Proves CatalogContext.cs uses CountAsync or count for pagination totals."""
        path = os.path.join(
            self.REPO_DIR, "src/Catalog.API/Infrastructure/CatalogContext.cs"
        )
        content = self._read(path)
        found = "CountAsync" in content or "count" in content.lower()
        assert found, "No count query found in CatalogContext.cs for pagination total"

    def test_catalog_service_active_cache_usage(self):
        """Proves CatalogService.cs actively calls cache methods, not just declares a field."""
        path = os.path.join(self.REPO_DIR, "src/Catalog.API/Services/CatalogService.cs")
        content = self._read(path)
        indicators = ["GetOrCreate", "cache.Get", "TryGetValue", "_cache"]
        found = [i for i in indicators if i in content]
        assert found, (
            f"Cache interface declared but never used in CatalogService.cs. "
            f"Expected one of {indicators}"
        )

    def test_catalog_context_eager_loading_or_projections(self):
        """Proves CatalogContext.cs uses Include() or .Select() to prevent N+1 queries."""
        path = os.path.join(
            self.REPO_DIR, "src/Catalog.API/Infrastructure/CatalogContext.cs"
        )
        content = self._read(path)
        found = "Include(" in content or ".Select(" in content
        assert found, (
            "No Include() or .Select() found in CatalogContext.cs — "
            "risk of N+1 queries or over-fetching"
        )
